"""Forms module."""
# pylint: disable=too-few-public-methods, missing-docstring
from typing import Any, Dict, Tuple
from flask_wtf import FlaskForm
from wtforms.fields import BooleanField, FieldList, StringField, TextAreaField, HiddenField
from wtforms.validators import DataRequired, InputRequired, ValidationError
from buku import DELIM, parse_tags
from bukuserver import _, _l, LazyString
from bukuserver.response import Response

def validate_tag(form, field):
    if not isinstance(field.data, str):
        raise ValidationError(_('Tag must be a string.'))
    if DELIM in field.data:
        raise ValidationError(_('Tag must not contain delimiter "%(delim)s".', delim=DELIM))


class SearchBookmarksForm(FlaskForm):
    keywords = FieldList(StringField(_l('Keywords')), min_entries=1)
    all_keywords = BooleanField(_l('Match all keywords'), default=True, description=_l('Exclude partial matches (with multiple keywords)'))
    markers = BooleanField(_l('With markers'), default=True, description=LazyString(lambda: '\n'.join([
        _('The search string will be split into multiple keywords, each will be applied to a field based on prefix:'),
        _(" - keywords starting with '.', '>' or ':' will be searched for in title, description and URL respectively"),
        _(" - '#' will be searched for in tags (comma-separated, partial matches; not affected by Deep Search)"),
        _(" - '#,' is the same but will match FULL tags only"),
        _(" - '*' will be searched for in all fields (this prefix can be omitted in the 1st keyword)"),
        _('Keywords need to be separated by placing spaces before the prefix.'),
    ])))
    deep = BooleanField(_l('Deep search'), description=_l('When unset, only FULL words will be matched.'))
    regex = BooleanField(_l('Regex'), description=_l('The keyword(s) are regular expressions (overrides other options).'))


class HomeForm(SearchBookmarksForm):
    keyword = StringField(_l('Keyword'))


class BookmarkForm(FlaskForm):
    url = StringField(_l('URL'), name='link', validators=[InputRequired()])
    title = StringField(_l('Title'))
    tags = StringField(_l('Tags'))
    description = TextAreaField(_l('Description'))
    fetch = HiddenField(filters=[bool])


class ApiTagForm(FlaskForm):
    class Meta:
        csrf = False

    tags = FieldList(StringField(validators=[DataRequired(), validate_tag]), min_entries=1)

    tags_str = None

    def process_data(self, data: Dict[str, Any]) -> Tuple[Response, Dict[str, Any]]:
        """Generate comma-separated string tags_str based on list of tags."""
        tags = data.get('tags')
        if tags and not isinstance(tags, list):
            return Response.INPUT_NOT_VALID, {'errors': {'tags': _('List of tags expected.')}}

        super().process(data=data)
        if not self.validate():
            return Response.INPUT_NOT_VALID, {'errors': self.errors}

        self.tags_str = None if tags is None else parse_tags([DELIM.join(tags)])
        return None, None


class ApiBookmarkCreateForm(ApiTagForm):
    class Meta:
        csrf = False

    url = StringField(validators=[DataRequired()])
    title = StringField()
    description = StringField()
    tags = FieldList(StringField(validators=[validate_tag]), min_entries=0)
    fetch = HiddenField(filters=[bool], default=True)


class ApiBookmarkEditForm(ApiBookmarkCreateForm):
    url = StringField()


class ApiBookmarkRangeEditForm(ApiBookmarkEditForm):

    del_tags = BooleanField(_('Delete tags list from existing tags'), default=False)

    tags_in = None

    def process_data(self, data: Dict[str, Any]) -> Tuple[Response, Dict[str, Any]]:
        """Generate comma-separated string tags_in based on list of tags."""
        error_response, data = super().process_data(data)

        if self.tags_str is not None:
            self.tags_in = ("-" if self.del_tags.data else "+") + self.tags_str

        return error_response, data
