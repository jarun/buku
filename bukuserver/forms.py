"""Forms module."""
# pylint: disable=too-few-public-methods, missing-docstring
from typing import Any, Dict, Tuple
from flask_wtf import FlaskForm
from wtforms.fields import BooleanField, FieldList, StringField, TextAreaField, HiddenField
from wtforms.validators import DataRequired, InputRequired, ValidationError
from buku import DELIM, parse_tags
from bukuserver.response import Response

def validate_tag(form, field):
    if not isinstance(field.data, str):
        raise ValidationError('Tag must be a string.')
    if DELIM in field.data:
        raise ValidationError('Tag must not contain delimiter \"{}\".'.format(DELIM))


class SearchBookmarksForm(FlaskForm):
    keywords = FieldList(StringField('Keywords'), min_entries=1)
    all_keywords = BooleanField('Match all keywords')
    deep = BooleanField('Deep search')
    regex = BooleanField('Regex')


class HomeForm(SearchBookmarksForm):
    keyword = StringField('Keyword')


class BookmarkForm(FlaskForm):
    url = StringField('Url', name='link', validators=[InputRequired()])
    title = StringField()
    tags = StringField()
    description = TextAreaField()
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
            return Response.INPUT_NOT_VALID, {'errors': {'tags': 'List of tags expected.'}}

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

    del_tags = BooleanField('Delete tags list from existing tags', default=False)

    tags_in = None

    def process_data(self, data: Dict[str, Any]) -> Tuple[Response, Dict[str, Any]]:
        """Generate comma-separated string tags_in based on list of tags."""
        error_response, data = super().process_data(data)

        if self.tags_str is not None:
            self.tags_in = ("-" if self.del_tags.data else "+") + self.tags_str

        return error_response, data
