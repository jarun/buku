"""Forms module."""
# pylint: disable=too-few-public-methods, missing-docstring
from flask_wtf import FlaskForm
from wtforms import StringField, FieldList, BooleanField, validators


class SearchBookmarksForm(FlaskForm):
    keywords = FieldList(StringField('Keywords'), min_entries=1)
    all_keywords = BooleanField('Match all keywords')
    deep = BooleanField('Deep search')
    regex = BooleanField('Regex')


class CreateBookmarksForm(FlaskForm):
    url = StringField(validators=[validators.required(), validators.URL(require_tld=False)])
    title = StringField()
    tags = StringField()
    description = StringField()
