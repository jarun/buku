from collections import Counter
from types import SimpleNamespace
from urllib.parse import urlparse
import logging

from flask import flash
from flask_admin.babel import gettext
from flask_admin.model import BaseModelView
from flask_wtf import FlaskForm
from jinja2 import Markup
import wtforms

try:
    from . import forms, filters as bs_filters
    from .filters import BookmarkField, FilterType
except ImportError:
    from bukuserver import forms, filters as bs_filters
    from bukuserver.filters import BookmarkField, FilterType


DEFAULT_URL_RENDER_MODE = 'full'
DEFAULT_PER_PAGE = 10
log = logging.getLogger("bukuserver.views")


class CustomBukuDbModel:  # pylint: disable=too-few-public-methods

    def __init__(self, bukudb_inst, name):
        self.bukudb = bukudb_inst
        self.name = name

    @property
    def __name__(self):
        return self.name


class BookmarkModelView(BaseModelView):

    def _apply_filters(self, models, filters):
        for idx, flt_name, value in filters:
            flt = self._filters[idx]
            clean_value = flt.clean(value)
            models = list(flt.apply(models, clean_value))
        return models

    def _create_ajax_loader(self, name, options):
        pass

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
        for tag in model.tags.split(','):
            if tag:
                res += '<a class="btn btn-default" href="#">{0}</a>'.format(tag)
        description = model.description
        if description:
            res += '<br/>'
            res += description.replace('\n', '<br/>')
        return Markup(res)

    can_set_page_size = True
    can_view_details = True
    column_filters = ['id', 'url', 'tags']
    column_formatters = {'Entry': _list_entry,}
    column_list = ['Entry']
    create_template = 'bukuserver/bookmark_create.html'
    details_modal = True
    edit_template = 'bukuserver/bookmark_edit.html'
    named_filter_urls = True

    def __init__(self, *args, **kwargs):
        self.bukudb = args[0]
        custom_model = CustomBukuDbModel(args[0], 'bookmark')
        args = [custom_model, ] + list(args[1:])
        self.page_size = kwargs.pop('page_size', DEFAULT_PER_PAGE)
        self.url_render_mode = kwargs.pop('url_render_mode', DEFAULT_URL_RENDER_MODE)
        super().__init__(*args, **kwargs)

    def create_model(self, form):
        try:
            model = SimpleNamespace(id=None, url=None, title=None, tags=None, description=None)
            form.populate_obj(model)
            vars(model).pop('id')
            self._on_model_change(form, model, True)
            tags_in = model.tags
            if not tags_in.startswith(','):
                tags_in = ',{}'.format(tags_in)
            if not tags_in.endswith(','):
                tags_in = '{},'.format(tags_in)
            self.model.bukudb.add_rec(
                url=model.url, title_in=model.title, tags_in=tags_in, desc=model.description)
        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash(gettext('Failed to create record. %(error)s', error=str(ex)), 'error')
                log.exception('Failed to create record.')
            return False
        else:
            self.after_model_change(form, model, True)
        return model

    def delete_model(self, model):
        try:
            self.on_model_delete(model)
            res = self.bukudb.delete_rec(model.id)
        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash(gettext('Failed to delete record. %(error)s', error=str(ex)), 'error')
                log.exception('Failed to delete record.')
            return False
        else:
            self.after_model_delete(model)
        return res

    def get_list(self, page, sort_field, sort_desc, search, filters, page_size=None):
        bukudb = self.bukudb
        all_bookmarks = bukudb.get_rec_all()
        all_bookmarks = self._apply_filters(all_bookmarks, filters)
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
                    value = bookmark[field.value]
                    if value.startswith(','):
                        value = value[1:]
                    if value.endswith(','):
                        value = value[:-1]
                    setattr(bm_sns, field.name.lower(), value)
                else:
                    setattr(bm_sns, field.name.lower(), bookmark[field.value])
            data.append(bm_sns)
        return count, data

    def get_one(self, id):
        bookmark = self.model.bukudb.get_rec_by_id(id)
        bm_sns = SimpleNamespace(id=None, url=None, title=None, tags=None, description=None)
        for field in list(BookmarkField):
            if field == BookmarkField.TAGS and bookmark[field.value].startswith(','):
                value = bookmark[field.value]
                if value.startswith(','):
                    value = value[1:]
                if value.endswith(','):
                    value = value[:-1]
                setattr(bm_sns, field.name.lower(), value)
            else:
                setattr(bm_sns, field.name.lower(), bookmark[field.value])
        return bm_sns

    def get_pk_value(self, model):
        return model.id

    def scaffold_list_columns(self):
        return [x.name.lower() for x in BookmarkField]

    def scaffold_list_form(self, widget=None, validators=None):
        pass

    def scaffold_sortable_columns(self):
        return {x:x for x in self.scaffold_list_columns()}

    def scaffold_filters(self, name):
        res = []
        if name == BookmarkField.ID.name.lower():
            res.extend([
                bs_filters.BookmarkBaseFilter(name, filter_type=FilterType.EQUAL),
                bs_filters.BookmarkBaseFilter(name, filter_type=FilterType.NOT_EQUAL),
                bs_filters.BookmarkBaseFilter(name, filter_type=FilterType.IN_LIST),
                bs_filters.BookmarkBaseFilter(name, filter_type=FilterType.NOT_IN_LIST),
                bs_filters.BookmarkBaseFilter(name, filter_type=FilterType.GREATER),
                bs_filters.BookmarkBaseFilter(name, filter_type=FilterType.SMALLER),
                bs_filters.BookmarkBaseFilter(name, filter_type=FilterType.TOP_X),
                bs_filters.BookmarkBaseFilter(name, filter_type=FilterType.BOTTOM_X),
            ])
        elif name == BookmarkField.URL.name.lower():
            def netloc_match_func(query, value, index):
                return filter(lambda x: urlparse(x[index]).netloc == value, query)

            res.extend([
                bs_filters.BookmarkBaseFilter(name, 'netloc match', netloc_match_func),
                bs_filters.BookmarkBaseFilter(name, filter_type=FilterType.EQUAL),
                bs_filters.BookmarkBaseFilter(name, filter_type=FilterType.NOT_EQUAL),
                bs_filters.BookmarkBaseFilter(name, filter_type=FilterType.IN_LIST),
                bs_filters.BookmarkBaseFilter(name, filter_type=FilterType.NOT_IN_LIST),
            ])
        elif name == BookmarkField.TAGS.name.lower():
            def tags_contain_func(query, value, index):
                for item in query:
                    for tag in item[index].split(','):
                        if tag and tag == value:
                            yield item

            def tags_not_contain_func(query, value, index):
                for item in query:
                    for tag in item[index].split(','):
                        if tag and tag == value:
                            yield item

            res.extend([
                bs_filters.BookmarkBaseFilter(name, 'contain', tags_contain_func),
                bs_filters.BookmarkBaseFilter(name, 'not contain', tags_not_contain_func),
                bs_filters.BookmarkTagNumberEqualFilter(name, 'number equal'),
                bs_filters.BookmarkTagNumberNotEqualFilter(name, 'number not equal'),
                bs_filters.BookmarkTagNumberGreaterFilter(name, 'number greater than'),
                bs_filters.BookmarkTagNumberSmallerFilter(name, 'number smaller than'),
            ])
        elif name in self.scaffold_list_columns():
            pass
        else:
            return super().scaffold_filters(name)
        return res

    def scaffold_form(self):
        cls = forms.BookmarkForm
        return cls

    def update_model(self, form, model):
        res = False
        try:
            original_tags = model.tags
            form.populate_obj(model)
            self._on_model_change(form, model, False)
            self.bukudb.delete_tag_at_index(model.id, original_tags)
            tags_in = model.tags
            if not tags_in.startswith(','):
                tags_in = ',{}'.format(tags_in)
            if not tags_in.endswith(','):
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

    def _create_ajax_loader(self, name, options):
        pass

    def _apply_filters(self, models, filters):
        for idx, flt_name, value in filters:
            flt = self._filters[idx]
            clean_value = flt.clean(value)
            models = list(flt.apply(models, clean_value))
        return models

    can_create = False
    column_filters = ['name', 'usage_count']

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
        class CustomForm(FlaskForm):  # pylint: disable=too-few-public-methods
            name = wtforms.StringField(validators=[wtforms.validators.required()])

        return CustomForm

    def scaffold_list_form(self, widget=None, validators=None):
        pass

    def get_list(self, page, sort_field, sort_desc, search, filters, page_size=None):
        bukudb = self.bukudb
        tags = bukudb.get_tag_all()[1]
        tags = [(x, y) for x, y in tags.items()]
        tags = self._apply_filters(tags, filters)
        if sort_field == 'usage_count':
            tags = sorted(tags, key=lambda x: x[1], reverse=sort_desc)
        elif sort_field == 'name':
            tags = sorted(tags, key=lambda x: x[0], reverse=sort_desc)
        tags = list(tags)
        count = len(tags)
        if page_size and tags:
            tags = list(chunks(tags, page_size))[page]
        data = []
        for name, usage_count in tags:
            tag_sns = SimpleNamespace(name=None, usage_count=None)
            tag_sns.name, tag_sns.usage_count = name, usage_count
            data.append(tag_sns)
        return count, data

    def get_pk_value(self, model):
        return model.name

    def get_one(self, id):
        tags = self.bukudb.get_tag_all()[1]
        tag_sns = SimpleNamespace(name=id, usage_count=tags[id])
        return tag_sns

    def scaffold_filters(self, name):
        res = []

        def top_most_common_func(query, value, index):
            counter = Counter(x[index] for x in query)
            most_common = counter.most_common(value)
            most_common_item = [x[0] for x in most_common]
            return filter(lambda x: x[index] in most_common_item, query)

        res.extend([
            bs_filters.TagBaseFilter(name, filter_type=FilterType.EQUAL),
            bs_filters.TagBaseFilter(name, filter_type=FilterType.NOT_EQUAL),
            bs_filters.TagBaseFilter(name, filter_type=FilterType.IN_LIST),
            bs_filters.TagBaseFilter(name, filter_type=FilterType.NOT_IN_LIST),
        ])
        if name == 'usage_count':
            res.extend([
                bs_filters.TagBaseFilter(name, filter_type=FilterType.GREATER),
                bs_filters.TagBaseFilter(name, filter_type=FilterType.SMALLER),
                bs_filters.TagBaseFilter(name, filter_type=FilterType.TOP_X),
                bs_filters.TagBaseFilter(name, filter_type=FilterType.BOTTOM_X),
                bs_filters.TagBaseFilter(name, 'top most common', top_most_common_func),
            ])
        elif name == 'name':
            pass
        else:
            return super().scaffold_filters(name)
        return res

    def delete_model(self, model):
        res = None
        try:
            self.on_model_delete(model)
            res = self.bukudb.delete_tag_at_index(0, model.name, chatty=False)
        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash(gettext('Failed to delete record. %(error)s', error=str(ex)), 'error')
                log.exception('Failed to delete record.')
            return False
        else:
            self.after_model_delete(model)
        return res

    def update_model(self, form, model):
        res = None
        try:
            original_name = model.name
            form.populate_obj(model)
            self._on_model_change(form, model, False)
            res = self.bukudb.replace_tag(original_name, [model.name])
        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash(gettext('Failed to update record. %(error)s', error=str(ex)), 'error')
                log.exception('Failed to update record.')
            return False
        else:
            self.after_model_change(form, model, False)
        return res

    def create_model(self, form):
        pass


def chunks(l, n):
    n = max(1, n)
    return (l[i:i+n] for i in range(0, len(l), n))
