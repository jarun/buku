"""views module."""
import functools
import itertools
import logging
import types
from argparse import Namespace
from collections import Counter, namedtuple
from typing import Any, List, Optional, Tuple
from urllib.parse import urlparse

import arrow
import wtforms
from flask import current_app, flash, redirect, request, session, url_for
from flask_admin.babel import gettext
from flask_admin.base import AdminIndexView, BaseView, expose
from flask_admin.model import BaseModelView
from flask_wtf import FlaskForm
from markupsafe import Markup, escape

import buku

try:
    from . import filters as bs_filters
    from . import forms
    from .filters import BookmarkField, FilterType
except ImportError:
    from bukuserver import filters as bs_filters  # type: ignore
    from bukuserver import forms
    from bukuserver.filters import BookmarkField, FilterType  # type: ignore


COLORS = ['#F7464A', '#46BFBD', '#FDB45C', '#FEDCBA', '#ABCDEF', '#DDDDDD',
          '#ABCABC', '#4169E1', '#C71585', '#FF4500', '#FEDCBA', '#46BFBD']
DEFAULT_URL_RENDER_MODE = 'full'
DEFAULT_PER_PAGE = 10
LOG = logging.getLogger('bukuserver.views')


class CustomAdminIndexView(AdminIndexView):
    @expose("/")
    def index(self):
        return self.render("bukuserver/home.html", form=forms.HomeForm())

    @expose('/', methods=['POST'])
    def search(self):
        "redirect to bookmark search"
        form = forms.HomeForm()
        buku_filter = bs_filters.BookmarkBukuFilter(deep=form.deep.data, regex=form.regex.data)
        url = url_for('bookmark.index_view', **{filter_key(buku_filter): form.keyword.data})
        return redirect(url)


def last_page(self):
    """Generic '/last_page' endpoint handler; based on
    https://github.com/flask-admin/flask-admin/blob/v1.6.0/flask_admin/model/base.py#L1956-L1969 """
    # Grab parameters from URL
    view_args = self._get_list_extra_args()

    # Map column index to column name
    sort_column = self._get_column_by_idx(view_args.sort)
    if sort_column is not None:
        sort_column = sort_column[0]

    # Get page size
    page_size = view_args.page_size or self.page_size

    # Get count and data
    count, data = self.get_list(-1, sort_column, view_args.sort_desc,
                                view_args.search, view_args.filters, page_size=page_size)

    args = request.args.copy()
    args.setlist('page', [max(0, (count - 1) // page_size)])
    return redirect(url_for('.index_view', **args))


def readonly_check(self):
    if current_app.config.get("BUKUSERVER_READONLY", False):
        self.can_create = False
        self.can_edit = False
        self.can_delete = False


class BookmarkModelView(BaseModelView):
    @staticmethod
    def _filter_arg(flt):
        """Exposes filter slugify logic; works because BookmarkModelView.named_filter_urls = True"""
        return BaseModelView.get_filter_arg(BookmarkModelView, None, flt)

    def _saved(self, id, url, ok=True):
        if id and ok:
            session['saved'] = id
        else:
            raise ValueError('Duplicate URL' if self.model.bukudb.get_rec_id(url) not in [id, None] else
                             'Rejected by the database')

    def _apply_filters(self, models, filters):
        for idx, _, value in filters:
            if self._filters:
                flt = self._filters[idx]
                clean_value = flt.clean(value)
                models = list(flt.apply(models, clean_value))
        return models

    def _create_ajax_loader(self, name, options):
        pass

    def _list_entry(self, context: Any, model: Namespace, name: str) -> Markup:
        LOG.debug("context: %s, name: %s", context, name)
        parsed_url = urlparse(model.url)
        netloc = parsed_url.netloc
        get_index_view_url = functools.partial(url_for, "bookmark.index_view")
        res = []
        if netloc and not current_app.config.get("BUKUSERVER_DISABLE_FAVICON", False):
            res += [f'<img class="favicon" src="http://www.google.com/s2/favicons?domain={netloc}"/> ']
        title = model.title or '<EMPTY TITLE>'
        new_tab = current_app.config.get("BUKUSERVER_OPEN_IN_NEW_TAB", False)
        url_for_index_view_netloc = None
        if netloc:
            url_for_index_view_netloc = get_index_view_url(flt0_url_netloc_match=netloc)
        if netloc and parsed_url.scheme:
            res += [f'<span class="title">{link(title, model.url, new_tab=new_tab)}</span>']
        else:
            res += [f'<span class="title">{escape(title)}</span>']
        if self.url_render_mode == 'netloc' and url_for_index_view_netloc:
            res += [f'<span class="netloc"> ({link(netloc, url_for_index_view_netloc)})</span>']
        if not parsed_url.scheme:
            res += [f'<span class="link">{escape(model.url)}</span>']
        elif self.url_render_mode is None or self.url_render_mode == 'full':
            res += [f'<span class="link">{link(model.url, model.url, new_tab=new_tab)}</span>']
        tag_links = []
        if netloc and self.url_render_mode != 'netloc' and url_for_index_view_netloc:
            tag_links += [link(f'netloc:{netloc}', url_for_index_view_netloc, badge='success')]
        for tag in filter(None, model.tags.split(',')):
            tag_links += [link(tag, get_index_view_url(flt0_tags_contain=tag.strip()), badge='default')]
        res += [f'<div class="tag-list">{"".join(tag_links)}</div>']
        description = model.description and f'<div class="description">{escape(model.description)}</div>'
        if description:
            res += [description]
        return Markup("".join(res))

    can_set_page_size = True
    can_view_details = True
    column_filters = ["buku", "id", "url", "title", "tags"]
    column_formatters = {
        "Entry": _list_entry,
    }
    column_list = ["Entry"]
    list_template = 'bukuserver/bookmarks_list.html'
    create_modal = True
    create_modal_template = "bukuserver/bookmark_create_modal.html"
    create_template = "bukuserver/bookmark_create.html"
    details_modal = True
    details_modal_template = 'bukuserver/bookmark_details_modal.html'
    details_template = 'bukuserver/bookmark_details.html'
    edit_modal = True
    edit_modal_template = "bukuserver/bookmark_edit_modal.html"
    edit_template = "bukuserver/bookmark_edit.html"
    named_filter_urls = True
    extra_css = ['/static/bukuserver/css/' + it for it in ('bookmark.css', 'modal.css')]
    extra_js = ['/static/bukuserver/js/' + it for it in ('page_size.js', 'last_page.js')]
    last_page = expose('/last-page')(last_page)

    def __init__(self, bukudb: buku.BukuDb, *args, **kwargs):
        readonly_check(self)
        self.bukudb = bukudb
        custom_model = types.SimpleNamespace(bukudb=bukudb, __name__='bookmark')
        super().__init__(custom_model, *args, **kwargs)

    @property
    def page_size(self):
        return current_app.config.get('BUKUSERVER_PER_PAGE', DEFAULT_PER_PAGE)

    @property
    def url_render_mode(self):
        return current_app.config.get('BUKUSERVER_URL_RENDER_MODE', DEFAULT_URL_RENDER_MODE)

    def create_form(self, obj=None):
        form = super().create_form(obj)
        if not form.data.get('csrf_token'):  # don't override POST data with URL arguments
            form.url.data = request.args.get('link', form.url.data)
            form.title.data = request.args.get('title', form.title.data)
            form.description.data = request.args.get('description', form.description.data)
        return form

    def create_model(self, form):
        try:
            model = types.SimpleNamespace(id=None, url=None, title=None, tags=None, description=None, fetch=True)
            form.populate_obj(model)
            vars(model).pop("id")
            self._on_model_change(form, model, True)
            if not model.url:
                raise ValueError(f"url invalid: {model.url}")
            kwargs = {'url': model.url, 'fetch': model.fetch}
            if model.tags.strip():
                kwargs["tags_in"] = buku.parse_tags([model.tags])
            for key, item in (("title_in", model.title), ("desc", model.description)):
                if item.strip():
                    kwargs[key] = item
            vars(model)['id'] = self.model.bukudb.add_rec(**kwargs)
            self._saved(model.id, model.url)
        except Exception as ex:
            if not self.handle_view_exception(ex):
                msg = "Failed to create record."
                flash(
                    gettext("%(msg)s %(error)s", msg=msg, error=str(ex)),
                    "error",
                )
                LOG.exception(msg)
            return False
        self.after_model_change(form, model, True)
        return model

    def delete_model(self, model):
        try:
            self.on_model_delete(model)
            res = self.bukudb.delete_rec(model.id)
        except Exception as ex:
            if not self.handle_view_exception(ex):
                msg = "Failed to delete record."
                flash(
                    gettext("%(msg)s %(error)s", msg=msg, error=str(ex)),
                    "error",
                )
                LOG.exception(msg)
            return False
        self.after_model_delete(model)
        return res

    def get_list(self, page, sort_field, sort_desc, _, filters, page_size=None):
        bukudb = self.bukudb
        buku_filters = [x for x in filters if x[1] == 'buku']
        if buku_filters:
            keywords = [x[2] for x in buku_filters]
            mode_id = {x[0] for x in buku_filters}
            if len(mode_id) > 1:
                flash(gettext("Invalid search mode combination"), "error")
                return 0, []
            try:
                kwargs = self._filters[mode_id.pop()].params
            except IndexError:
                kwargs = {}
            bookmarks = bukudb.searchdb(keywords, **kwargs)
        else:
            bookmarks = bukudb.get_rec_all()
        bookmarks = self._apply_filters(bookmarks or [], filters)
        count = len(bookmarks)
        bookmarks = page_of(bookmarks, page_size, page)
        data = []
        for bookmark in bookmarks:
            bm_sns = types.SimpleNamespace(id=None, url=None, title=None, tags=None, description=None)
            for field in list(BookmarkField):
                setattr(bm_sns, field.name.lower(), format_value(field, bookmark))
            data.append(bm_sns)
        return count, data

    def get_one(self, id):
        bookmark = self.model.bukudb.get_rec_by_id(id)
        if bookmark is None:
            return None
        bm_sns = types.SimpleNamespace(id=None, url=None, title=None, tags=None, description=None)
        for field in list(BookmarkField):
            setattr(bm_sns, field.name.lower(), format_value(field, bookmark, spacing=' '))
        session['netloc'] = urlparse(bookmark.url).netloc
        return bm_sns

    def get_pk_value(self, model):
        return model.id

    def scaffold_list_columns(self):
        return [x.name.lower() for x in BookmarkField]

    def scaffold_list_form(self, widget=None, validators=None):
        pass

    def scaffold_sortable_columns(self):
        """Returns a dictionary of sortable columns.

        from flask-admin docs:
        `If your backend does not support sorting, return None or an empty dictionary.`
        """
        return {}

    def scaffold_filters(self, name):
        res = []
        if name == "buku":
            values_combi = sorted(itertools.product([True, False], repeat=3))
            for all_keywords, deep, regex in values_combi:
                res.append(
                    bs_filters.BookmarkBukuFilter(
                        all_keywords=all_keywords, deep=deep, regex=regex
                    )
                )
        elif name == BookmarkField.ID.name.lower():
            res += [
                bs_filters.BookmarkBaseFilter(name, filter_type=FilterType.EQUAL),
                bs_filters.BookmarkBaseFilter(name, filter_type=FilterType.NOT_EQUAL),
                bs_filters.BookmarkBaseFilter(name, filter_type=FilterType.IN_LIST),
                bs_filters.BookmarkBaseFilter(name, filter_type=FilterType.NOT_IN_LIST),
                bs_filters.BookmarkBaseFilter(name, filter_type=FilterType.GREATER),
                bs_filters.BookmarkBaseFilter(name, filter_type=FilterType.SMALLER),
                bs_filters.BookmarkBaseFilter(name, filter_type=FilterType.TOP_X),
                bs_filters.BookmarkBaseFilter(name, filter_type=FilterType.BOTTOM_X),
            ]
        elif name == BookmarkField.URL.name.lower():

            def netloc_match_func(query, value, index):
                return filter(lambda x: urlparse(x[index]).netloc == value, query)

            res += [
                bs_filters.BookmarkBaseFilter(name, "netloc match", netloc_match_func),
                bs_filters.BookmarkBaseFilter(name, filter_type=FilterType.EQUAL),
                bs_filters.BookmarkBaseFilter(name, filter_type=FilterType.NOT_EQUAL),
                bs_filters.BookmarkBaseFilter(name, filter_type=FilterType.IN_LIST),
                bs_filters.BookmarkBaseFilter(name, filter_type=FilterType.NOT_IN_LIST),
                bs_filters.BookmarkBaseFilter(name, filter_type=FilterType.CONTAINS),
                bs_filters.BookmarkBaseFilter(name, filter_type=FilterType.NOT_CONTAINS),
            ]
        elif name == BookmarkField.TITLE.name.lower():
            res += [
                bs_filters.BookmarkBaseFilter(name, filter_type=FilterType.EQUAL),
                bs_filters.BookmarkBaseFilter(name, filter_type=FilterType.NOT_EQUAL),
                bs_filters.BookmarkBaseFilter(name, filter_type=FilterType.IN_LIST),
                bs_filters.BookmarkBaseFilter(name, filter_type=FilterType.NOT_IN_LIST),
                bs_filters.BookmarkBaseFilter(name, filter_type=FilterType.CONTAINS),
                bs_filters.BookmarkBaseFilter(name, filter_type=FilterType.NOT_CONTAINS),
            ]
        elif name == BookmarkField.TAGS.name.lower():

            def get_list_from_buku_tags(item):
                return [x.strip() for x in item.split(",")]

            def tags_contain_func(query, value, index):
                for item in query:
                    if value in get_list_from_buku_tags(item[index]):
                        yield item

            def tags_not_contain_func(query, value, index):
                for item in query:
                    if value not in get_list_from_buku_tags(item[index]):
                        yield item

            res += [
                bs_filters.BookmarkBaseFilter(name, "contain", tags_contain_func),
                bs_filters.BookmarkBaseFilter(name, "not contain", tags_not_contain_func),
                bs_filters.BookmarkTagNumberEqualFilter(name, "number equal"),
                bs_filters.BookmarkTagNumberNotEqualFilter(name, "number not equal"),
                bs_filters.BookmarkTagNumberGreaterFilter(name, "number greater than"),
                bs_filters.BookmarkTagNumberSmallerFilter(name, "number smaller than"),
            ]
        elif name in self.scaffold_list_columns():
            pass
        else:
            return super().scaffold_filters(name)
        return res

    def scaffold_form(self):
        cls = forms.BookmarkForm
        return cls

    def update_model(self, form: forms.BookmarkForm, model: Namespace):
        res = False
        try:
            form.populate_obj(model)
            self._on_model_change(form, model, False)
            res = self.bukudb.update_rec(
                model.id,
                url=model.url,
                title_in=model.title,
                tags_in=buku.parse_tags([model.tags]),
                desc=model.description,
            )
            self._saved(model.id, model.url, res)
        except Exception as ex:
            if not self.handle_view_exception(ex):
                msg = "Failed to update record."
                flash(
                    gettext("%(msg)s %(error)s", msg=msg, error=str(ex)),
                    "error",
                )
                LOG.exception(msg)
            return False
        self.after_model_change(form, model, False)
        return res


class TagModelView(BaseModelView):
    def _create_ajax_loader(self, name, options):
        pass

    def _apply_filters(self, models, filters):
        for idx, _, value in filters:
            if self._filters:
                flt = self._filters[idx]
                clean_value = flt.clean(value)
                models = list(flt.apply(models, clean_value))
        return models

    def _name_formatter(self, _, model, name):
        data = getattr(model, name)
        query, title = (({'flt0_tags_contain': data}, data) if data else
                        ({'flt0_tags_number_equal': 0}, '<UNTAGGED>'))
        return Markup(link(title, url_for("bookmark.index_view", **query)))

    can_create = False
    can_set_page_size = True
    column_filters = ["name", "usage_count"]
    column_formatters = {
        "name": _name_formatter,
    }
    list_template = 'bukuserver/tags_list.html'
    extra_js = ['/static/bukuserver/js/' + it for it in ('page_size.js', 'last_page.js')]
    last_page = expose('/last-page')(last_page)

    def __init__(self, bukudb, *args, **kwargs):
        readonly_check(self)
        self.bukudb = bukudb
        self.all_tags = self.bukudb.get_tag_all()
        custom_model = types.SimpleNamespace(bukudb=bukudb, __name__='tag')
        super().__init__(custom_model, *args, **kwargs)

    @property
    def page_size(self):
        return current_app.config.get('BUKUSERVER_PER_PAGE', DEFAULT_PER_PAGE)

    @expose('/refresh', methods=['POST'])
    def refresh(self):
        self.all_tags = self.bukudb.get_tag_all()
        return redirect(request.referrer or url_for('.index_view'))

    def scaffold_list_columns(self):
        return ["name", "usage_count"]

    def scaffold_sortable_columns(self):
        return {x: x for x in self.scaffold_list_columns()}

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
        page_size: int = None,
    ) -> Tuple[int, List[types.SimpleNamespace]]:
        logging.debug("search: %s", search)
        tags = self._apply_filters(sorted(self.all_tags[1].items()), filters)
        sort_field_dict = {"usage_count": 1, "name": 0}
        if sort_field in sort_field_dict:
            tags = list(
                sorted(
                    tags,
                    key=lambda x: x[sort_field_dict[sort_field]],
                    reverse=sort_desc,
                )
            )
        count = len(tags)
        tags = page_of(tags, page_size, page)
        data = []
        for name, usage_count in tags:
            tag_sns = types.SimpleNamespace(name=None, usage_count=None)
            tag_sns.name, tag_sns.usage_count = name, usage_count
            data.append(tag_sns)
        return count, data

    def get_pk_value(self, model):
        return model.name

    def get_one(self, id):
        tags = self.all_tags[1]
        tag_sns = types.SimpleNamespace(name=id, usage_count=tags[id])
        return tag_sns

    def scaffold_filters(self, name):
        res = []

        def top_most_common_func(query, value, index):
            counter = Counter(x[index] for x in query)
            most_common = counter.most_common(value)
            most_common_item = [x[0] for x in most_common]
            return filter(lambda x: x[index] in most_common_item, query)

        res += [
            bs_filters.TagBaseFilter(name, filter_type=FilterType.EQUAL),
            bs_filters.TagBaseFilter(name, filter_type=FilterType.NOT_EQUAL),
            bs_filters.TagBaseFilter(name, filter_type=FilterType.IN_LIST),
            bs_filters.TagBaseFilter(name, filter_type=FilterType.NOT_IN_LIST),
            bs_filters.TagBaseFilter(name, filter_type=FilterType.CONTAINS),
            bs_filters.TagBaseFilter(name, filter_type=FilterType.NOT_CONTAINS),
        ]
        if name == "usage_count":
            res += [
                bs_filters.TagBaseFilter(name, filter_type=FilterType.GREATER),
                bs_filters.TagBaseFilter(name, filter_type=FilterType.SMALLER),
                bs_filters.TagBaseFilter(name, filter_type=FilterType.TOP_X),
                bs_filters.TagBaseFilter(name, filter_type=FilterType.BOTTOM_X),
                bs_filters.TagBaseFilter(name, "top most common", top_most_common_func),
            ]
        elif name == "name":
            pass
        else:
            return super().scaffold_filters(name)
        return res

    def delete_model(self, model):
        res = None
        try:
            self.on_model_delete(model)
            res = self.bukudb.delete_tag_at_index(0, model.name, chatty=False)
            self.all_tags = self.bukudb.get_tag_all()
        except Exception as ex:
            if not self.handle_view_exception(ex):
                msg = "Failed to delete record."
                flash(
                    gettext("%(msg)s %(error)s", msg=msg, error=str(ex)),
                    "error",
                )
                LOG.exception(msg)
            return False
        self.after_model_delete(model)
        return res

    def update_model(self, form, model):
        try:
            original_name = model.name
            form.populate_obj(model)
            self._on_model_change(form, model, False)
            self.bukudb.replace_tag(original_name, [model.name])
            self.all_tags = self.bukudb.get_tag_all()
        except Exception as ex:
            if not self.handle_view_exception(ex):
                msg = "Failed to update record."
                flash(
                    gettext("%(msg)s %(error)s", msg=msg, error=str(ex)),
                    "error",
                )
                LOG.exception(msg)
            return False
        self.after_model_change(form, model, False)
        return True

    def create_model(self, form):
        pass


class StatisticView(BaseView):  # pylint: disable=too-few-public-methods
    _data = None
    extra_css = ['/static/bukuserver/css/modal.css']

    def __init__(self, bukudb, *args, **kwargs):
        self.bukudb = bukudb
        super().__init__(*args, **kwargs)

    @expose("/", methods=("GET", "POST"))
    def index(self):
        data = StatisticView._data
        if not data or request.method == 'POST':
            all_bookmarks = self.bukudb.get_rec_all()
            netlocs = [urlparse(x.url).netloc for x in all_bookmarks]
            tags = [s for x in all_bookmarks for s in x.taglist]
            titles = [x.title for x in all_bookmarks]
            data = StatisticView._data = {
                'netlocs': sorted_counter(netlocs),
                'tags': sorted_counter(tags),
                'titles': sorted_counter(titles, min_count=1),
                'generated': arrow.now(),
            }

        datetime = data['generated']
        return self.render(
            'bukuserver/statistic.html',
            netlocs=CountedData(data['netlocs']),
            tags=CountedData(data['tags']),
            titles=CountedData(data['titles']),
            datetime=datetime,
            datetime_text=datetime.humanize(arrow.now(), granularity='second'),
        )


def chunks(arr, n):
    n = max(1, n)
    return [arr[i : i + n] for i in range(0, len(arr), n)]

def page_of(items, size, idx):
    try:
        return chunks(items, size)[idx] if size and items else items
    except IndexError:
        return []

def filter_key(flt, idx=''):
    return 'flt' + str(idx) + '_' + BookmarkModelView._filter_arg(flt)

def format_value(field, bookmark, spacing=''):
    s = bookmark[field.value]
    return s if field != BookmarkField.TAGS else (s or '').strip(',').replace(',', ','+spacing)

def link(text, url, new_tab=False, badge=''):
    target = ('' if not new_tab else ' target="_blank"')
    cls = ('' if not badge else f' class="btn label label-{badge}"')
    return f'<a{cls} href="{escape(url)}"{target}>{escape(text)}</a>'

def sorted_counter(keys, *, min_count=0):
    data = Counter(keys)
    return Counter({k: v for k, v in sorted(data.items()) if v > min_count})


ColoredData = namedtuple('ColoredData', 'name amount color')

class CountedData(list):
    def __init__(self, counter):
        self._counter = Counter(counter)
        data = self._counter.most_common(len(COLORS))
        self += [ColoredData(name, amount, color) for (name, amount), color in zip(data, COLORS)]

    @property
    def cropped(self):
        return len(self) < len(self._counter)

    @property
    def all(self):
        return self._counter.most_common()
