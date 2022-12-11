"""Forms module."""
# pylint: disable=too-few-public-methods, missing-docstring
import wtforms
from flask_wtf import FlaskForm


class SearchBookmarksForm(FlaskForm):
    keywords = wtforms.FieldList(wtforms.StringField('Keywords'), min_entries=1)
    all_keywords = wtforms.BooleanField('Match all keywords')
    deep = wtforms.BooleanField('Deep search')
    regex = wtforms.BooleanField('Regex')


class HomeForm(SearchBookmarksForm):
    keyword = wtforms.StringField('Keyword')


class BookmarkForm(FlaskForm):
    url = wtforms.StringField('Url', name='link', validators=[wtforms.validators.DataRequired()])
    title = wtforms.StringField()
    tags = wtforms.StringField()
    description = wtforms.TextAreaField()
    fetch = wtforms.HiddenField(filters=[bool])

class ApiBookmarkForm(BookmarkForm):
    url = wtforms.StringField(validators=[wtforms.validators.DataRequired()])
