from enum import Enum
from collections import namedtuple
from urllib.parse import urlparse

from flask_admin.model import BaseModelView
from jinja2 import Markup

try:
    from . import forms
except ImportError:
    from bukuserver import forms


DEFAULT_URL_RENDER_MODE = 'full'
DEFAULT_PER_PAGE = 10


class CustomBukuDbModel:

    def __init__(self, bukudb_inst, name):
        self.bukudb = bukudb_inst
        self.name = name

    @property
    def __name__(self):
        return self.name


class BookmarkField(Enum):
    ID = 0
    URL = 1
    TITLE = 2
    TAGS = 3
    DESCRIPTION = 4


class BookmarkModelView(BaseModelView):

    def _list_entry(self, context, model, name):
        netloc = urlparse(model.url).netloc
        if netloc:
            res = '<img src="http://www.google.com/s2/favicons?domain={}"/>'.format(netloc)
        else:
            res = ''
        res += '<a href="{0.url}">{0.title}</a>'.format(model)
        if self.url_render_mode == 'netloc':
            res += ' ({})'.format(netloc)
        res += '<br/>'
        if self.url_render_mode is None or self.url_render_mode == 'full':
            res += '<a href="{0.url}">{0.url}</a>'.format(model)
            res += '<br/>'
        for tag in model.tags:
            res += '<a class="btn btn-default" href="#">{0}</a>'.format(tag)
        res += '<br/>'
        res += model.description
        return Markup(res)

    #  column_list = [x.name.lower() for x in BookmarkField] + ['Entry']
    column_list = ['Entry']
    #  column_exclude_list = ['description', ]
    column_formatters = {'Entry': _list_entry,}
    list_template = 'bukuserver/bookmark_list.html'
    can_view_details = True

    def __init__(self, *args, **kwargs):
        self.bukudb = args[0]
        custom_model = CustomBukuDbModel(args[0], 'bookmark')
        args = [custom_model, ] + list(args[1:])
        self.page_size = kwargs.pop('page_size', DEFAULT_PER_PAGE)
        self.url_render_mode = kwargs.pop('url_render_mode', DEFAULT_URL_RENDER_MODE)
        super().__init__(*args, **kwargs)

    def scaffold_list_columns(self):
        return [x.name.lower() for x in BookmarkField]

    def scaffold_sortable_columns(self):
        return {x:x for x in self.scaffold_list_columns()}

    def scaffold_form(self):
        return forms.BookmarkForm

    def get_list(self, page, sort_field, sort_desc, search, filters, page_size=None):
        bukudb = self.bukudb
        all_bookmarks = bukudb.get_rec_all()
        if sort_field:
            key_idx = [x.value for x in BookmarkField if x.name.lower() == sort_field][0]
            all_bookmarks = sorted(all_bookmarks, key=lambda x:x[key_idx], reverse=sort_desc)
        count = len(all_bookmarks)
        data = []
        bookmarks = list(chunks(all_bookmarks, page_size))[page]
        for bookmark in bookmarks:
            data.append(convert_bookmark_dict_to_namedtuple(bookmark))
        return count, data

    def get_pk_value(self, model):
        return model.id

    def get_one(self, id):
        bookmark = self.model.bukudb.get_rec_by_id(id)
        res = convert_bookmark_dict_to_namedtuple(bookmark)
        return res


def convert_bookmark_dict_to_namedtuple(bookmark_dict):
    bookmark = bookmark_dict
    keys = [x.name.lower() for x in BookmarkField]
    Bm = namedtuple('Bookmark', keys)
    result_bookmark = {}
    for field in list(BookmarkField):
        if field == BookmarkField.TAGS:
            result_bookmark[field.name.lower()] = list(
                [f for f in bookmark[field.value].split(',') if f])
        else:
            result_bookmark[field.name.lower()] = bookmark[field.value]
    return Bm(**result_bookmark)


def chunks(l, n):
    n = max(1, n)
    return (l[i:i+n] for i in range(0, len(l), n))
