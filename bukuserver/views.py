from collections import namedtuple
from enum import Enum
from urllib.parse import urlparse
import logging
from types import SimpleNamespace

from flask import flash
from flask_admin.babel import gettext
from flask_admin.model import BaseModelView
from flask_wtf import FlaskForm
from jinja2 import Markup, escape
import wtforms

try:
    from . import forms
except ImportError:
    from bukuserver import forms


DEFAULT_URL_RENDER_MODE = 'full'
DEFAULT_PER_PAGE = 10
log = logging.getLogger("bukuserver.views")


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
            netloc_tmpl = '<img src="{}{}"/> '
            res = netloc_tmpl.format(
                'http://www.google.com/s2/favicons?domain=', netloc)
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
        description = model.description
        if description:
            res += '<br/>'
            res += description.replace('\n', '<br/>')
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
        cls = forms.BookmarkForm
        tags = self.bukudb.get_tag_all()[0]
        tags = zip(tags, tags)
        cls.tags.kwargs.setdefault('choices', []).extend(tags)
        return cls

    def get_list(self, page, sort_field, sort_desc, search, filters, page_size=None):
        bukudb = self.bukudb
        all_bookmarks = bukudb.get_rec_all()
        if sort_field:
            key_idx = [x.value for x in BookmarkField if x.name.lower() == sort_field][0]
            all_bookmarks = sorted(all_bookmarks, key=lambda x:x[key_idx], reverse=sort_desc)
        count = len(all_bookmarks)
        if page_size:
            bookmarks = list(chunks(all_bookmarks, page_size))[page]
        data = []
        for bookmark in bookmarks:
            bm_sns = SimpleNamespace(id=None, url=None, title=None, tags=None, description=None)
            for field in list(BookmarkField):
                if field == BookmarkField.TAGS:
                    setattr(
                        bm_sns, field.name.lower(),
                        list(set(x for x in bookmark[field.value].split(',') if x)))
                else:
                    setattr(bm_sns, field.name.lower(), bookmark[field.value])
            data.append(bm_sns)
        return count, data

    def get_pk_value(self, model):
        return model.id

    def get_one(self, id):
        bookmark = self.model.bukudb.get_rec_by_id(id)
        bm_sns = SimpleNamespace(id=None, url=None, title=None, tags=None, description=None)
        for field in list(BookmarkField):
            if field == BookmarkField.TAGS:
                setattr(
                    bm_sns, field.name.lower(),
                    list(set(x for x in bookmark[field.value].split(',') if x)))
            else:
                setattr(bm_sns, field.name.lower(), bookmark[field.value])
        return bm_sns

    def update_model(self, form, model):
        res = False
        try:
            form.populate_obj(model)
            self._on_model_change(form, model, False)
            tags_in = ', '.join(model.tags)
            if tags_in.startswith(','):
                tags_in = ',{}'.format(tags_in)
            if tags_in.endswith(','):
                tags_in = '{},'.format(tags_in)
            res = self.bukudb.update_rec(
                model.id, url=model.url, title_in=model.title, tags_in=tags_in,
                desc=model.description)
        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash(gettext('Failed to update record. %(error)s', error=str(ex)), 'error')
                log.exception('Failed to update record.')
            return False
        else:
            self.after_model_change(form, model, False)
        return res


class TagModelView(BaseModelView):

    can_create = False
    can_delete = False

    def __init__(self, *args, **kwargs):
        self.bukudb = args[0]
        custom_model = CustomBukuDbModel(args[0], 'tag')
        args = [custom_model, ] + list(args[1:])
        self.page_size = kwargs.pop('page_size', DEFAULT_PER_PAGE)
        super().__init__(*args, **kwargs)

    def scaffold_list_columns(self):
        return ['name', 'usage_count']

    def scaffold_sortable_columns(self):
        return {x:x for x in self.scaffold_list_columns()}

    def scaffold_form(self):
        class CustomForm(FlaskForm):
            name = wtforms.StringField(validators=[wtforms.validators.required()])

        return CustomForm

    def get_list(self, page, sort_field, sort_desc, search, filters, page_size=None):
        bukudb = self.bukudb
        tags = bukudb.get_tag_all()[1]
        tags = [(x, y) for x, y in tags.items()]
        if sort_field == 'usage_count':
            tags = sorted(tags, key=lambda x: x[1], reverse=sort_desc)
        elif sort_field == 'name':
            tags = sorted(tags, key=lambda x: x[0], reverse=sort_desc)
        count = len(tags)
        tag_nt = namedtuple('Tag', ['name', 'usage_count'])
        if page_size:
            tags = list(chunks(tags, page_size))[page]
        data = []
        for name, usage_count in tags:
            data.append(tag_nt(name=name, usage_count=usage_count))
        return count, data

    def get_pk_value(self, model):
        return model.name

    def get_one(self, id):
        tags = self.bukudb.get_tag_all()[1]
        tag_nt = namedtuple('Tag', ['name', 'usage_count'])
        return tag_nt(name=id, usage_count=tags[id])


def chunks(l, n):
    n = max(1, n)
    return (l[i:i+n] for i in range(0, len(l), n))