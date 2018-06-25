"""Forms module."""
# pylint: disable=too-few-public-methods, missing-docstring
from flask_wtf import FlaskForm
import wtforms


class SearchBookmarksForm(FlaskForm):
    keywords = wtforms.FieldList(wtforms.StringField('Keywords'), min_entries=1)
    all_keywords = wtforms.BooleanField('Match all keywords')
    deep = wtforms.BooleanField('Deep search')
    regex = wtforms.BooleanField('Regex')


class TagsField(wtforms.StringField):

    def __call__(self, **kwargs):
        #  self.render_kw = {'multiple': 'multiple', 'class': 'select2-multiple'}
        return super().__call__(**kwargs)


class BookmarkForm(FlaskForm):
    url = wtforms.StringField(
        validators=[wtforms.validators.required(), wtforms.validators.URL(require_tld=False)])
    title = wtforms.StringField()
    tags = TagsField()
    description = wtforms.TextAreaField()
