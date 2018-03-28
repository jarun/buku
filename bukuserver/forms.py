from flask_wtf import FlaskForm
from wtforms import StringField, FieldList, validators, BooleanField


class SearchBookmarksForm(FlaskForm):
    keywords = FieldList(StringField('Keywords'), min_entries=1)
    all_keywords = BooleanField('Match all keywords')
    deep = BooleanField('Deep search')
    regex = BooleanField('Regex')
