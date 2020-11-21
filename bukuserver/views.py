"""views module."""
from argparse import Namespace
from collections import Counter
from types import SimpleNamespace
from typing import Any, List, Optional, Tuple
from urllib.parse import urlparse
import itertools
import logging

from flask import current_app, flash, redirect, request, url_for
from flask_admin.babel import gettext
from flask_admin.base import AdminIndexView, BaseView, expose
from flask_admin.model import BaseModelView
from flask_wtf import FlaskForm
from jinja2 import Markup
import arrow
import wtforms

try:
    from . import forms, filters as bs_filters
    from .filters import BookmarkField, FilterType
except ImportError:
    from bukuserver import forms, filters as bs_filters
    from bukuserver.filters import BookmarkField, FilterType


STATISTIC_DATA = None
DEFAULT_URL_RENDER_MODE = 'full'
DEFAULT_PER_PAGE = 10
LOG = logging.getLogger("bukuserver.views")


class CustomAdminIndexView(AdminIndexView):

    @expose('/')
    def index(self):
        return self.render('bukuserver/home.html', form=forms.HomeForm())

    @expose('/', methods=['POST',])
    def search(self):
        "redirect to bookmark search"
        form = forms.HomeForm()
        bbm_filter = bs_filters.BookmarkBukuFilter(
            all_keywords=False, deep=form.deep.data, regex=form.regex.data)
        op_text = bbm_filter.operation()
        values_combi = sorted(itertools.product([True, False], repeat=3))
        for idx, (all_keywords, deep, regex) in enumerate(values_combi):
            if deep == form.deep.data and regex == form.regex.data and not all_keywords:
                choosen_idx = idx
        url_op_text = op_text.replace(', ', '_').replace('  ', ' ').replace(' ', '_')
        key = ''.join(['flt', str(choosen_idx), '_buku_', url_op_text])
        kwargs = {key: form.keyword.data}
        url = url_for('bookmark.index_view', **kwargs)
        return redirect(url)


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

    def _list_entry(
            self, context: Any, model: Namespace, name: str) -> Markup:
        parsed_url = urlparse(model.url)
        netloc, scheme = parsed_url.netloc, parsed_url.scheme
        is_scheme_valid = scheme in ('http', 'https')
        tag_text = []
        tag_tmpl = '<a class="btn btn-default" href="{1}">{0}</a>'
        for tag in model.tags.split(','):
            if tag:
                tag_text.append(tag_tmpl.format(tag, url_for(
                    'bookmark.index_view', flt2_tags_contain=tag)))
        if not netloc:
            return Markup("""\
            {0.title}<br/>{2}<br/>{1}{0.description}
            """.format(
                model, ''.join(tag_text), Markup.escape(model.url)
            ))
        res = ''
        if not current_app.config.get('BUKUSERVER_DISABLE_FAVICON', False):
            netloc_tmpl = '<img src="{}{}"/> '
            res = netloc_tmpl.format(
                'http://www.google.com/s2/favicons?domain=', netloc)
        title = model.title if model.title else '&lt;EMPTY TITLE&gt;'
        open_in_new_tab = current_app.config.get('BUKUSERVER_OPEN_IN_NEW_TAB', False)
        if is_scheme_valid and open_in_new_tab:
            res += '<a href="{0.url}" target="_blank">{1}</a>'.format(model, title)
        elif is_scheme_valid and not open_in_new_tab:
            res += '<a href="{0.url}">{1}</a>'.format(model, title)
        else:
            res += title
        if self.url_render_mode == 'netloc':
            res += ' (<a href="{1}">{0}</a>)'.format(
                netloc,
                url_for('bookmark.index_view', flt2_url_netloc_match=netloc)
            )
        res += '<br/>'
        if not is_scheme_valid:
            res += model.url
        elif self.url_render_mode is None or self.url_render_mode == 'full':
            res += '<a href="{0.url}">{0.url}</a>'.format(model)
            res += '<br/>'
        if self.url_render_mode != 'netloc':
            res += tag_tmpl.format(
                'netloc:{}'.format(netloc),
                url_for('bookmark.index_view', flt2_url_netloc_match=netloc)
            )
        res += ''.join(tag_text)
        description = model.description
        if description:
            res += '<br/>'
            res += description.replace('\n', '<br/>')
        return Markup(res)

    can_set_page_size = True
    can_view_details = True
    column_filters = ['buku', 'id', 'url', 'title', 'tags']
    column_formatters = {'Entry': _list_entry,}
    column_list = ['Entry']
    create_modal = True
    create_modal_template = 'bukuserver/bookmark_create_modal.html'
    create_template = 'bukuserver/bookmark_create.html'
    details_modal = True
    edit_modal = True
    edit_modal_template = 'bukuserver/bookmark_edit_modal.html'
    edit_template = 'bukuserver/bookmark_edit.html'
    named_filter_urls = True

    def __init__(self, *args, **kwargs):
        self.bukudb = args[0]
        custom_model = CustomBukuDbModel(args[0], 'bookmark')
        args = [custom_model, ] + list(args[1:])
        self.page_size = kwargs.pop('page_size', DEFAULT_PER_PAGE)
        self.url_render_mode = kwargs.pop('url_render_mode', DEFAULT_URL_RENDER_MODE)
        super().__init__(*args, **kwargs)

    def create_form(self, obj=None):
        form = super().create_form(obj)
        args = request.args
        if 'url' in args.keys() and not args.get("url").startswith('/bookmark/'):
            form.url.data = args.get("url")
        if 'title' in args.keys():
            form.title.data = args.get("title")
        if 'description' in args.keys():
            form.description.data = args.get("description")
        return form

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
                LOG.exception('Failed to create record.')
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
                LOG.exception('Failed to delete record.')
            return False
        else:
            self.after_model_delete(model)
        return res

    def get_list(self, page, sort_field, sort_desc, search, filters, page_size=None):
        bukudb = self.bukudb
        contain_buku_search = any(x[1] == 'buku' for x in filters)
        if contain_buku_search:
            mode_id = [x[0] for x in filters]
            if len(list(set(mode_id))) > 1:
                flash(gettext('Invalid search mode combination'), 'error')
                return 0, []
            keywords = [x[2] for x in filters]
            for idx, flt_name, value in filters:
                if flt_name == 'buku':
                    flt = self._filters[idx]
            bookmarks = bukudb.searchdb(
                keywords, all_keywords=flt.all_keywords, deep=flt.deep, regex=flt.regex)
        else:
            bookmarks = bukudb.get_rec_all()
        bookmarks = self._apply_filters(bookmarks, filters)
        if sort_field:
            key_idx = [x.value for x in BookmarkField if x.name.lower() == sort_field][0]
            bookmarks = sorted(bookmarks, key=lambda x: x[key_idx], reverse=sort_desc)
        count = len(bookmarks)
        if page_size and bookmarks:
            try:
                bookmarks = list(chunks(bookmarks, page_size))[page]
            except IndexError:
                bookmarks = []
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
        if name == 'buku':
            values_combi = sorted(itertools.product([True, False], repeat=3))
            for all_keywords, deep, regex in values_combi:
                res.append(
                    bs_filters.BookmarkBukuFilter(all_keywords=all_keywords, deep=deep, regex=regex)
                )
        elif name == BookmarkField.ID.name.lower():
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
        elif name == BookmarkField.TITLE.name.lower():
            res.extend([
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
                LOG.exception('Failed to update record.')
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

    def _name_formatter(self, context, model, name):
        data = getattr(model, name)
        if not data:
            return Markup('<a href="{}">{}</a>'.format(
                url_for('bookmark.index_view', flt2_tags_number_equal=0),
                '&lt;EMPTY TAG&gt;'
            ))
        return Markup('<a href="{}">{}</a>'.format(
            url_for('bookmark.index_view', flt1_tags_contain=data), data
        ))

    can_create = False
    can_set_page_size = True
    column_filters = ['name', 'usage_count']
    column_formatters = {'name': _name_formatter,}

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
            name = wtforms.StringField(validators=[wtforms.validators.DataRequired()])

        return CustomForm

    def scaffold_list_form(self, widget=None, validators=None):
        pass

    def get_list(
            self,
            page: int,
            sort_field: str,
            sort_desc: bool,
            search: Optional[Any],
            filters: List[Tuple[int, str, str]],
            page_size: int = None) -> Tuple[int, List[SimpleNamespace]]:
        bukudb = self.bukudb
        tags = bukudb.get_tag_all()[1]
        tags = sorted(tags.items())
        tags = self._apply_filters(tags, filters)
        sort_field_dict = {'usage_count': 1, 'name': 0}
        if sort_field in sort_field_dict:
            tags = list(sorted(
                tags, key=lambda x: x[sort_field_dict[sort_field]], reverse=sort_desc))
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
                LOG.exception('Failed to delete record.')
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
                LOG.exception('Failed to update record.')
            return False
        else:
            self.after_model_change(form, model, False)
        return res

    def create_model(self, form):
        pass


class StatisticView(BaseView):  # pylint: disable=too-few-public-methods

    def __init__(self, *args, **kwargs):
        self.bukudb = args[0]
        args = list(args[1:])
        super().__init__(*args, **kwargs)

    @expose('/', methods=('GET', 'POST'))
    def index(self):
        bukudb = self.bukudb
        global STATISTIC_DATA
        statistic_data = STATISTIC_DATA
        if not statistic_data or request.method == 'POST':
            all_bookmarks = bukudb.get_rec_all()
            netloc = [urlparse(x[1]).netloc for x in all_bookmarks]
            tag_set = [x[3] for x in all_bookmarks]
            tag_items = []
            for tags in tag_set:
                tag_items.extend([x.strip() for x in tags.split(',') if x.strip()])
            tag_counter = Counter(tag_items)
            title_items = [x[2] for x in all_bookmarks]
            title_counter = Counter(title_items)
            statistic_datetime = arrow.now()
            STATISTIC_DATA = {
                'datetime': statistic_datetime,
                'netloc': netloc,
                'tag_counter': tag_counter,
                'title_counter': title_counter,
            }
        else:
            netloc = statistic_data['netloc']
            statistic_datetime = statistic_data['datetime']
            tag_counter = statistic_data['tag_counter']
            title_counter = statistic_data['title_counter']

        netloc_counter = Counter(netloc)
        unique_netloc_len = len(set(netloc))
        colors = [
            "#F7464A", "#46BFBD", "#FDB45C", "#FEDCBA",
            "#ABCDEF", "#DDDDDD", "#ABCABC", "#4169E1",
            "#C71585", "#FF4500", "#FEDCBA", "#46BFBD"]
        show_netloc_table = False
        if unique_netloc_len > len(colors):
            max_netloc_item = len(colors)
            netloc_colors = colors
            show_netloc_table = True
        else:
            netloc_colors = colors[:unique_netloc_len]
            max_netloc_item = unique_netloc_len
        most_common_netlocs = netloc_counter.most_common(max_netloc_item)
        most_common_netlocs = [
            [val[0], val[1], netloc_colors[idx]] for idx, val in enumerate(most_common_netlocs)]

        unique_tag_len = len(tag_counter)
        show_tag_rank_table = False
        if unique_tag_len > len(colors):
            max_tag_item = len(colors)
            tag_colors = colors
            show_tag_rank_table = True
        else:
            tag_colors = colors[:unique_tag_len]
            max_tag_item = unique_tag_len
        most_common_tags = tag_counter.most_common(max_tag_item)
        most_common_tags = [
            [val[0], val[1], tag_colors[idx]] for idx, val in enumerate(most_common_tags)]

        unique_title_len = len(title_counter)
        show_title_rank_table = False
        if unique_title_len > len(colors):
            max_title_item = len(colors)
            title_colors = colors
            show_title_rank_table = True
        else:
            title_colors = colors[:unique_title_len]
            max_title_item = unique_title_len
        most_common_titles = title_counter.most_common(max_title_item)
        most_common_titles = [
            [val[0], val[1], title_colors[idx]] for idx, val in enumerate(most_common_titles)]

        return self.render(
            'bukuserver/statistic.html',
            most_common_netlocs=most_common_netlocs,
            netloc_counter=netloc_counter,
            show_netloc_table=show_netloc_table,
            most_common_tags=most_common_tags,
            tag_counter=tag_counter,
            show_tag_rank_table=show_tag_rank_table,
            most_common_titles=most_common_titles,
            title_counter=title_counter,
            show_title_rank_table=show_title_rank_table,
            datetime=statistic_datetime,
            datetime_text=statistic_datetime.humanize(arrow.now(), granularity='second'),
        )


def chunks(arr, n):
    n = max(1, n)
    return (arr[i:i+n] for i in range(0, len(arr), n))
