#!/usr/bin/env python
# pylint: disable=wrong-import-order, ungrouped-imports
"""Server module."""
from typing import Any, Dict, Union  # NOQA; type: ignore
from unittest import mock
from urllib.parse import urlparse
import os
import sys

from buku import BukuDb, __version__, network_handler
from flask.cli import FlaskGroup
from flask.views import MethodView
from flask_admin import Admin
from flask_api import exceptions, FlaskAPI, status
from flask_bootstrap import Bootstrap
from flask_paginate import Pagination, get_page_parameter, get_per_page_parameter
try:
    from flask_reverse_proxy_fix.middleware import ReverseProxyPrefixFix
except ImportError:
    ReverseProxyPrefixFix = None
from markupsafe import Markup
import click
import flask
from flask import (  # type: ignore
    __version__ as flask_version,
    abort,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

try:
    from . import response, forms, views
except ImportError:
    from bukuserver import response, forms, views


STATISTIC_DATA = None

def get_bukudb():
    """get bukudb instance"""
    db_file = current_app.config.get('BUKUSERVER_DB_FILE', None)
    return BukuDb(dbfile=db_file)

def get_tags():
    """get tags."""
    tags = getattr(flask.g, 'bukudb', get_bukudb()).get_tag_all()
    result = {
        'tags': tags[0]
    }
    if request.path.startswith('/api/'):
        res = jsonify(result)
    else:
        res = render_template('bukuserver/tags.html', result=result)
    return res


def handle_network():
    failed_resp = response.response_template['failure'], status.HTTP_400_BAD_REQUEST
    url = request.data.get('url', None)
    if not url:
        return failed_resp
    try:
        res = network_handler(url)
        keys = ['title', 'description', 'tags', 'recognized mime', 'bad url']
        res_dict = dict(zip(keys, res))
        return jsonify(res_dict)
    except Exception as e:
        current_app.logger.debug(str(e))
    return failed_resp


def update_tag(tag):
    res = None
    if request.method in ('PUT', 'POST'):
        new_tags = request.form.getlist('tags')
        result_flag = getattr(flask.g, 'bukudb', get_bukudb()).replace_tag(tag, new_tags)
        op_text = 'replace tag [{}] with [{}]'.format(tag, ', '.join(new_tags))
        if request.method == 'PUT' and result_flag and request.path.startswith('/api/'):
            res = (jsonify(response.response_template['success']),
                   status.HTTP_200_OK,
                   {'ContentType': 'application/json'})
        elif request.method == 'PUT' and request.path.startswith('/api/'):
            res = (jsonify(response.response_template['failure']),
                   status.HTTP_400_BAD_REQUEST,
                   {'ContentType': 'application/json'})
        elif request.method == 'POST' and result_flag:
            flash(Markup('Success {}'.format(op_text)), 'success')
            res = redirect(url_for('get_tags-html'))
        elif request.method == 'POST':
            flash(Markup('Failed {}'.format(op_text)), 'danger')
            res = redirect(url_for('get_tags-html'))
        else:
            abort(400, description="Unknown Condition")
    return res


def refresh_bookmark(rec_id: Union[int, None]):
    if rec_id is not None:
        result_flag = getattr(flask.g, 'bukudb', get_bukudb()).refreshdb(rec_id, request.form.get('threads', 4))
    else:
        result_flag = getattr(flask.g, 'bukudb', get_bukudb()).refreshdb(0, request.form.get('threads', 4))
    if result_flag:
        res = (jsonify(response.response_template['success']),
               status.HTTP_200_OK,
               {'ContentType': 'application/json'})
    else:
        res = (jsonify(response.response_template['failure']),
               status.HTTP_400_BAD_REQUEST,
               {'ContentType': 'application/json'})
    return res


def get_tiny_url(rec_id):
    shortened_url = getattr(flask.g, 'bukudb', get_bukudb()).tnyfy_url(rec_id)
    if shortened_url is not None:
        result = {'url': shortened_url}
        res = jsonify(result)
    else:
        res = (
            jsonify(response.response_template['failure']),
            status.HTTP_400_BAD_REQUEST,
            {'ContentType': 'application/json'})
    return res


def search_bookmarks():
    arg_obj = request.form if request.method == 'DELETE' else request.args
    search_bookmarks_form = forms.SearchBookmarksForm(request.args)
    is_api_request_path = request.path.startswith('/api/')
    if is_api_request_path:
        keywords = arg_obj.getlist('keywords')
        all_keywords = arg_obj.get('all_keywords')
        deep = arg_obj.get('deep')
        regex = arg_obj.get('regex')
        # api request is more strict
        all_keywords = False if all_keywords is None else all_keywords
        deep = False if deep is None else deep
        regex = False if regex is None else regex
        all_keywords = (
            all_keywords if isinstance(all_keywords, bool) else
            all_keywords.lower() == 'true'
        )
        deep = deep if isinstance(deep, bool) else deep.lower() == 'true'
        regex = regex if isinstance(regex, bool) else regex.lower() == 'true'
    else:
        keywords = search_bookmarks_form.keywords.data
        all_keywords = search_bookmarks_form.all_keywords.data
        deep = search_bookmarks_form.deep.data
        regex = search_bookmarks_form.regex.data

    result = {'bookmarks': []}
    bukudb = getattr(flask.g, 'bukudb', get_bukudb())
    found_bookmarks = bukudb.searchdb(keywords, all_keywords, deep, regex)
    found_bookmarks = [] if found_bookmarks is None else found_bookmarks
    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = request.args.get(
        get_per_page_parameter(),
        type=int,
        default=int(
            current_app.config.get('BUKUSERVER_PER_PAGE', views.DEFAULT_PER_PAGE))
    )

    res = None
    if request.method == 'GET':
        if found_bookmarks is not None:
            for bookmark in found_bookmarks:
                result_bookmark = {
                    'id': bookmark[0],
                    'url': bookmark[1],
                    'title': bookmark[2],
                    'tags': list([_f for _f in bookmark[3].split(',') if _f]),
                    'description': bookmark[4]
                }
                result['bookmarks'].append(result_bookmark)
        current_app.logger.debug('total bookmarks:{}'.format(len(result['bookmarks'])))
        if is_api_request_path:
            res = jsonify(result)
        else:
            pagination_total = len(result['bookmarks'])
            bms = list(views.chunks(result['bookmarks'], per_page))
            try:
                result['bookmarks'] = bms[page-1]
            except IndexError as err:
                current_app.logger.debug('{}:{}, result bookmarks:{}, page:{}'.format(
                    type(err), err, len(result['bookmarks']), page
                ))
            pagination = Pagination(
                page=page, total=pagination_total, per_page=per_page,
                search=False, record_name='bookmarks', bs_version=3
            )
            res = render_template(
                'bukuserver/bookmarks.html',
                result=result, pagination=pagination,
                search_bookmarks_form=search_bookmarks_form,
                create_bookmarks_form=forms.BookmarkForm(),
            )
    elif request.method == 'DELETE':
        if found_bookmarks is not None:
            for bookmark in found_bookmarks:
                result_flag = bukudb.delete_rec(bookmark[0])
                if result_flag is False:
                    res = (jsonify(response.response_template['failure']),
                           status.HTTP_400_BAD_REQUEST,
                           {'ContentType': 'application/json'})
        if res is None:
            res = (jsonify(response.response_template['success']),
                   status.HTTP_200_OK,
                   {'ContentType': 'application/json'})
    return res


def create_app(db_file=None):
    """create app."""
    app = FlaskAPI(__name__)
    per_page = int(os.getenv('BUKUSERVER_PER_PAGE', str(views.DEFAULT_PER_PAGE)))
    per_page = per_page if per_page > 0 else views.DEFAULT_PER_PAGE
    app.config['BUKUSERVER_PER_PAGE'] = per_page
    url_render_mode = os.getenv('BUKUSERVER_URL_RENDER_MODE', views.DEFAULT_URL_RENDER_MODE)
    if url_render_mode not in ('full', 'netloc'):
        url_render_mode = views.DEFAULT_URL_RENDER_MODE
    app.config['BUKUSERVER_URL_RENDER_MODE'] = url_render_mode
    app.config['SECRET_KEY'] = os.getenv('BUKUSERVER_SECRET_KEY') or os.urandom(24)
    disable_favicon = os.getenv('BUKUSERVER_DISABLE_FAVICON', 'false')
    app.config['BUKUSERVER_DISABLE_FAVICON'] = \
        False if disable_favicon.lower() in ['false', '0'] else bool(disable_favicon)
    open_in_new_tab = os.getenv('BUKUSERVER_OPEN_IN_NEW_TAB', 'false')
    app.config['BUKUSERVER_OPEN_IN_NEW_TAB'] = \
        False if open_in_new_tab.lower() in ['false', '0'] else bool(open_in_new_tab)
    app.config['BUKUSERVER_DB_FILE'] = os.getenv('BUKUSERVER_DB_FILE') or db_file
    reverse_proxy_path = os.getenv('BUKUSERVER_REVERSE_PROXY_PATH')
    if reverse_proxy_path:
        if not reverse_proxy_path.startswith('/'):
            print('Warning: reverse proxy path should include preceding slash')
        if reverse_proxy_path.endswith('/'):
            print('Warning: reverse proxy path should not include trailing slash')
        app.config['REVERSE_PROXY_PATH'] = reverse_proxy_path
        if ReverseProxyPrefixFix:
            ReverseProxyPrefixFix(app)
        else:
            raise ImportError('Failed to import ReverseProxyPrefixFix')
    bukudb = BukuDb(dbfile=app.config['BUKUSERVER_DB_FILE'])
    app.app_context().push()
    setattr(flask.g, 'bukudb', bukudb)

    @app.shell_context_processor
    def shell_context():
        """Shell context definition."""
        return {'app': app, 'bukudb': bukudb}

    app.jinja_env.filters['netloc'] = lambda x: urlparse(x).netloc  # pylint: disable=no-member

    Bootstrap(app)
    admin = Admin(
        app, name='buku server', template_mode='bootstrap3',
        index_view=views.CustomAdminIndexView(
            template='bukuserver/home.html', url='/'
        )
    )
    # routing
    #  api
    tag_api_view = ApiTagView.as_view('tag_api')
    app.add_url_rule('/api/tags', defaults={'tag': None}, view_func=tag_api_view, methods=['GET'])
    app.add_url_rule('/api/tags/<tag>', view_func=tag_api_view, methods=['GET', 'PUT'])
    bookmark_api_view = ApiBookmarkView.as_view('bookmark_api')
    app.add_url_rule('/api/bookmarks', defaults={'rec_id': None}, view_func=bookmark_api_view, methods=['GET', 'POST', 'DELETE'])
    app.add_url_rule('/api/bookmarks/<int:rec_id>', view_func=bookmark_api_view, methods=['GET', 'PUT', 'DELETE'])
    app.add_url_rule('/api/bookmarks/refresh', 'refresh_bookmark', refresh_bookmark, defaults={'rec_id': None}, methods=['POST'])
    app.add_url_rule('/api/bookmarks/<int:rec_id>/refresh', 'refresh_bookmark', refresh_bookmark, methods=['POST'])
    app.add_url_rule('/api/bookmarks/<int:rec_id>/tiny', 'get_tiny_url', get_tiny_url, methods=['GET'])
    app.add_url_rule('/api/network_handle', 'network_handle', handle_network, methods=['POST'])
    bookmark_range_api_view = ApiBookmarkRangeView.as_view('bookmark_range_api')
    app.add_url_rule(
        '/api/bookmarks/<int:starting_id>/<int:ending_id>',
        view_func=bookmark_range_api_view, methods=['GET', 'PUT', 'DELETE'])
    bookmark_search_api_view = ApiBookmarkSearchView.as_view('bookmark_search_api')
    app.add_url_rule('/api/bookmarks/search', view_func=bookmark_search_api_view, methods=['GET', 'DELETE'])
    bookmarklet_view = BookmarkletView.as_view('bookmarklet')
    app.add_url_rule('/bookmarklet', view_func=bookmarklet_view, methods=['GET'])
    #  non api
    admin.add_view(views.BookmarkModelView(
        bukudb, 'Bookmarks', page_size=per_page, url_render_mode=url_render_mode))
    admin.add_view(views.TagModelView(
        bukudb, 'Tags', page_size=per_page))
    admin.add_view(views.StatisticView(
        bukudb, 'Statistic', endpoint='statistic'))
    return app


class ApiTagView(MethodView):

    def get(self, tag: Union[str, None]):
        bukudb = get_bukudb()
        if tag is None:
            tags = bukudb.get_tag_all()
            result = {'tags': tags[0]}
            return result
        tags = bukudb.get_tag_all()
        if tag not in tags[1]:
            raise exceptions.NotFound()
        res = dict(name=tag, usage_count=tags[1][tag])
        return res

    def put(self, tag: str):
        bukudb = get_bukudb()
        res = None
        try:
            new_tags = request.data.get('tags')  # type: ignore
            if new_tags:
                new_tags = new_tags.split(',')
            else:
                return response.response_template['failure'], status.HTTP_400_BAD_REQUEST
        except AttributeError as e:
            raise exceptions.ParseError(detail=str(e))
        result_flag = bukudb.replace_tag(tag, new_tags)
        if result_flag:
            res = response.response_template['success'], status.HTTP_200_OK
        else:
            res = response.response_template['failure'], status.HTTP_400_BAD_REQUEST
        return res


class ApiBookmarkView(MethodView):

    def get(self, rec_id: Union[int, None]):
        if rec_id is None:
            bukudb = getattr(flask.g, 'bukudb', get_bukudb())
            all_bookmarks = bukudb.get_rec_all()
            result = {'bookmarks': []}  # type: Dict[str, Any]
            for bookmark in all_bookmarks:
                result_bookmark = {
                    'url': bookmark[1],
                    'title': bookmark[2],
                    'tags': list([_f for _f in bookmark[3].split(',') if _f]),
                    'description': bookmark[4]
                }
                if not request.path.startswith('/api/'):
                    result_bookmark['id'] = bookmark[0]
                result['bookmarks'].append(result_bookmark)
            res = jsonify(result)
        else:
            bukudb = getattr(flask.g, 'bukudb', get_bukudb())
            bookmark = bukudb.get_rec_by_id(rec_id)
            if bookmark is not None:
                result = {
                    'url': bookmark[1],
                    'title': bookmark[2],
                    'tags': list([_f for _f in bookmark[3].split(',') if _f]),
                    'description': bookmark[4]
                }
                res = jsonify(result)
            else:
                res = jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, \
                       {'ContentType': 'application/json'}
        return res

    def post(self, rec_id: None = None):
        bukudb = getattr(flask.g, 'bukudb', get_bukudb())
        create_bookmarks_form = forms.BookmarkForm()
        url_data = create_bookmarks_form.url.data
        result_flag = bukudb.add_rec(
            url_data,
            create_bookmarks_form.title.data,
            create_bookmarks_form.tags.data,
            create_bookmarks_form.description.data
        )
        if result_flag != -1:
            res = jsonify(response.response_template['success'])
        else:
            res = jsonify(response.response_template['failure'])
            res.status_code = status.HTTP_400_BAD_REQUEST
        return res

    def put(self, rec_id: int):
        bukudb = getattr(flask.g, 'bukudb', get_bukudb())
        result_flag = bukudb.update_rec(
            rec_id,
            request.form.get('url'),
            request.form.get('title'),
            request.form.get('tags'),
            request.form.get('description'))
        if result_flag:
            res = (jsonify(response.response_template['success']),
                   status.HTTP_200_OK,
                   {'ContentType': 'application/json'})
        else:
            res = (jsonify(response.response_template['failure']),
                   status.HTTP_400_BAD_REQUEST,
                   {'ContentType': 'application/json'})
        return res

    def delete(self, rec_id: Union[int, None]):
        if rec_id is None:
            bukudb = getattr(flask.g, 'bukudb', get_bukudb())
            with mock.patch('buku.read_in', return_value='y'):
                result_flag = bukudb.cleardb()
            if result_flag:
                res = jsonify(response.response_template['success'])
            else:
                res = jsonify(response.response_template['failure'])
                res.status_code = status.HTTP_400_BAD_REQUEST
        else:
            bukudb = getattr(flask.g, 'bukudb', get_bukudb())
            result_flag = bukudb.delete_rec(rec_id)
            if result_flag:
                res = (jsonify(response.response_template['success']),
                       status.HTTP_200_OK,
                       {'ContentType': 'application/json'})
            else:
                res = (jsonify(response.response_template['failure']),
                       status.HTTP_400_BAD_REQUEST,
                       {'ContentType': 'application/json'})
        return res


class ApiBookmarkRangeView(MethodView):

    def get(self, starting_id: int, ending_id: int):
        bukudb = getattr(flask.g, 'bukudb', get_bukudb())
        max_id = bukudb.get_max_id()
        if starting_id > max_id or ending_id > max_id:
            return jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, \
                   {'ContentType': 'application/json'}
        result = {'bookmarks': {}}  # type: ignore
        for i in range(starting_id, ending_id + 1, 1):
            bookmark = bukudb.get_rec_by_id(i)
            result['bookmarks'][i] = {
                'url': bookmark[1],
                'title': bookmark[2],
                'tags': list([_f for _f in bookmark[3].split(',') if _f]),
                'description': bookmark[4]
            }
        res = jsonify(result)
        return res

    def put(self, starting_id: int, ending_id: int):
        bukudb = getattr(flask.g, 'bukudb', get_bukudb())
        max_id = bukudb.get_max_id()
        if starting_id > max_id or ending_id > max_id:
            return jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, \
                   {'ContentType': 'application/json'}
        for i in range(starting_id, ending_id + 1, 1):
            updated_bookmark = request.data.get(str(i))  # type: ignore
            result_flag = bukudb.update_rec(
                i,
                updated_bookmark.get('url'),
                updated_bookmark.get('title'),
                updated_bookmark.get('tags'),
                updated_bookmark.get('description'))
            if result_flag is False:
                return (
                    jsonify(response.response_template['failure']),
                    status.HTTP_400_BAD_REQUEST,
                    {'ContentType': 'application/json'})
        res = jsonify(response.response_template['success'])
        return res

    def delete(self, starting_id: int, ending_id: int):
        bukudb = getattr(flask.g, 'bukudb', get_bukudb())
        max_id = bukudb.get_max_id()
        if starting_id > max_id or ending_id > max_id:
            return jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, \
                   {'ContentType': 'application/json'}
        idx = min([starting_id, ending_id])
        result_flag = bukudb.delete_rec(idx, starting_id, ending_id, is_range=True)
        if result_flag is False:
            res = jsonify(response.response_template['failure'])
            res.status_code = status.HTTP_400_BAD_REQUEST
        else:
            res = jsonify(response.response_template['success'])
        return res


class ApiBookmarkSearchView(MethodView):

    def get(self):
        arg_obj = request.args
        keywords = arg_obj.getlist('keywords')
        all_keywords = arg_obj.get('all_keywords')
        deep = arg_obj.get('deep')
        regex = arg_obj.get('regex')
        # api request is more strict
        all_keywords = False if all_keywords is None else all_keywords
        deep = False if deep is None else deep
        regex = False if regex is None else regex
        all_keywords = (
            all_keywords if isinstance(all_keywords, bool) else
            all_keywords.lower() == 'true'
        )
        deep = deep if isinstance(deep, bool) else deep.lower() == 'true'
        regex = regex if isinstance(regex, bool) else regex.lower() == 'true'

        result = {'bookmarks': []}
        bukudb = getattr(flask.g, 'bukudb', get_bukudb())
        found_bookmarks = bukudb.searchdb(keywords, all_keywords, deep, regex)
        found_bookmarks = [] if found_bookmarks is None else found_bookmarks
        res = None
        if found_bookmarks is not None:
            for bookmark in found_bookmarks:
                result_bookmark = {
                    'id': bookmark[0],
                    'url': bookmark[1],
                    'title': bookmark[2],
                    'tags': list([_f for _f in bookmark[3].split(',') if _f]),
                    'description': bookmark[4]
                }
                result['bookmarks'].append(result_bookmark)
        current_app.logger.debug('total bookmarks:{}'.format(len(result['bookmarks'])))
        res = jsonify(result)
        return res

    def delete(self):
        arg_obj = request.form
        keywords = arg_obj.getlist('keywords')
        all_keywords = arg_obj.get('all_keywords')
        deep = arg_obj.get('deep')
        regex = arg_obj.get('regex')
        # api request is more strict
        all_keywords = False if all_keywords is None else all_keywords
        deep = False if deep is None else deep
        regex = False if regex is None else regex
        all_keywords = (
            all_keywords if isinstance(all_keywords, bool) else
            all_keywords.lower() == 'true'
        )
        deep = deep if isinstance(deep, bool) else deep.lower() == 'true'
        regex = regex if isinstance(regex, bool) else regex.lower() == 'true'
        bukudb = getattr(flask.g, 'bukudb', get_bukudb())
        found_bookmarks = bukudb.searchdb(keywords, all_keywords, deep, regex)
        found_bookmarks = [] if found_bookmarks is None else found_bookmarks
        res = None
        if found_bookmarks is not None:
            for bookmark in found_bookmarks:
                result_flag = bukudb.delete_rec(bookmark[0])
                if result_flag is False:
                    res = jsonify(response.response_template['failure'])
                    res.status = status.HTTP_400_BAD_REQUEST
        if res is None:
            res = jsonify(response.response_template['success'])
        return res


class BookmarkletView(MethodView):
    def get(self):
        url = request.args.get('url')
        title = request.args.get('title')
        description = request.args.get('description')

        bukudb = getattr(flask.g, 'bukudb', get_bukudb())
        rec_id = bukudb.get_rec_id(url)
        if rec_id >= 0:
            return redirect(url_for('bookmark.edit_view', id=rec_id))
        return redirect(url_for('bookmark.create_view', url=url, title=title, description=description))


class CustomFlaskGroup(FlaskGroup):  # pylint: disable=too-few-public-methods
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.params[0].help = 'Show the program version'
        self.params[0].callback = get_custom_version


def get_custom_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    message = '%(app_name)s %(app_version)s\nFlask %(version)s\nPython %(python_version)s'
    click.echo(message % {
        'app_name': 'buku',
        'app_version': __version__,
        'version': flask_version,
        'python_version': sys.version,
    }, color=ctx.color)
    ctx.exit()


@click.group(cls=CustomFlaskGroup, create_app=create_app)
def cli():
    """This is a script for the bukuserver application."""


if __name__ == '__main__':
    cli()
