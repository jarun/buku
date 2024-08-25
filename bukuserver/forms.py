"""Forms module."""
# pylint: disable=too-few-public-methods, missing-docstring
import re
from flask_wtf import FlaskForm
from wtforms import Form
from wtforms.fields import BooleanField, FieldList, URLField, StringField, TextAreaField, HiddenField, SelectMultipleField
from wtforms.validators import DataRequired, InputRequired, Length, Regexp, StopValidation
from buku import DELIM, taglist_str
from bukuserver import _, _l, LazyString

_parse_bool = lambda x: str(x).lower() == 'true'

TAG_RE = re.compile(r'^[^,]*[^,\s]+[^,]*$')

def optional_none(form, field):
    if field.data is None:
        raise StopValidation()

def is_string(form, field):
    if not isinstance(field.data, str):
        raise StopValidation(_('The value must be a string.'))

validate_tag = [is_string, Regexp(TAG_RE)]


class ValueList(SelectMultipleField):
    """A form field model for simple value lists, capable of processing regular array data."""

    def __init__(self, *args, item_validators=[], **kwargs):
        self.data, self._valid, self._field = None, True, StringField(validators=item_validators)
        super().__init__(*args, choices=[], validate_choice=False, coerce=(lambda x: x), **kwargs)

    def process_data(self, value):
        self._valid = isinstance(value, (list, tuple, set, type(None)))  # i.e. for JSON input
        self.data = None
        if self._valid:
            super().process_data(value)

    def pre_validate(self, form):
        _errors = []
        _field = self._field.bind(form=form, name=self.name, _meta=self.meta, translations=self._translations)  # pylint: disable=no-member
        for item in (self.data or []):
            _field.data = item
            _field.validate(form)
            _errors += [_field.errors]
        if any(x for x in _errors):
            self.errors += _errors
        if not self._valid:
            raise StopValidation(self.gettext('Invalid input.'))


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
    url = URLField(_l('URL'), name='link', validators=[InputRequired()])
    title = StringField(_l('Title'))
    tags = StringField(_l('Tags'))
    description = TextAreaField(_l('Description'))
    fetch = HiddenField(filters=[bool])


class SwapForm(FlaskForm):
    id1 = HiddenField(filters=[int])
    id2 = HiddenField(filters=[int])


class ApiFetchDataForm(Form):
    url = StringField(validators=[DataRequired()])


class ApiTagForm(Form):
    tags = ValueList(validators=[DataRequired()], item_validators=validate_tag)

    @property
    def tags_str(self):
        return (None if self.tags.data is None else taglist_str(DELIM.join(self.tags.data)))


class ApiBookmarkCreateForm(ApiTagForm):
    url = StringField(validators=[DataRequired()])
    title = StringField()
    description = StringField()
    tags = ValueList(item_validators=validate_tag)
    fetch = BooleanField(filters=[_parse_bool])

    @property
    def data_values(self):
        return [self.url.data, self.title.data, self.description.data, self.tags.data]

    @property
    def has_data(self):
        return self.fetch.data or any(self.data_values)


class ApiBookmarkEditForm(ApiBookmarkCreateForm):
    url = StringField(validators=[optional_none, Length(min=1)])

    @property
    def has_data(self):  # allowing to delete existing values
        return self.fetch.data or any(x is not None for x in self.data_values)


class ApiBookmarkRangeEditForm(ApiBookmarkEditForm):
    del_tags = BooleanField(_('Delete tags list from existing tags'), default=False)

    @property
    def tags_in(self):
        return (None if not self.tags.data else ('-' if self.del_tags.data else '+') + self.tags_str)

    @property
    def data_values(self):  # ignoring empty tags list
        return [self.url.data, self.title.data, self.description.data, self.tags_in]


class ApiBookmarkSearchForm(Form):
    keywords = ValueList(validators=[DataRequired()], item_validators=[is_string])
    all_keywords = BooleanField(filters=[_parse_bool])
    deep = BooleanField(filters=[_parse_bool])
    regex = BooleanField(filters=[_parse_bool])
    markers = BooleanField(filters=[_parse_bool])
    order = ValueList(item_validators=[is_string])

class ApiBookmarksReorderForm(Form):
    order = ValueList(validators=[DataRequired()], item_validators=[is_string])
