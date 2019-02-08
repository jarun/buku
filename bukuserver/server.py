#!/usr/bin/env python
# pylint: disable=wrong-import-order, ungrouped-imports
"""Server module."""
import os
import sys
from urllib.parse import urlparse

from buku import BukuDb, __version__, network_handler
from flask.cli import FlaskGroup
from flask_admin import Admin
from flask_api import exceptions, FlaskAPI, status
from flask_bootstrap import Bootstrap
from flask_paginate import Pagination, get_page_parameter, get_per_page_parameter
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


def network_handle_detail():
    failed_resp = response.response_template['failure'], status.HTTP_400_BAD_REQUEST
    url = request.data.get('url', None)
    if not url:
        return failed_resp
    try:
        res = network_handler(url)
        return {'title': res[0], 'recognized mime': res[1], 'bad url': res[2]}
    except Exception as e:
        current_app.logger.debug(str(e))
    return failed_resp


def tag_list():
    tags = get_bukudb().get_tag_all()
    result = {'tags': tags[0]}
    return result


def tag_detail(tag):
    bukudb = get_bukudb()
    if request.method == 'GET':
        tags = bukudb.get_tag_all()
        if tag not in tags[1]:
            raise exceptions.NotFound()
        res = dict(name=tag, usage_count=tags[1][tag])
    elif request.method == 'PUT':
        res = None
        try:
            new_tags = request.data.get('tags').split(',')
        except AttributeError as e:
            raise exceptions.ParseError(detail=str(e))
        result_flag = bukudb.replace_tag(tag, new_tags)
        if result_flag:
            res = response.response_template['success'], status.HTTP_200_OK
        else:
            res = response.response_template['failure'], status.HTTP_400_BAD_REQUEST
    return res


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


def bookmarks():
    """Bookmarks."""
    res = None
    bukudb = getattr(flask.g, 'bukudb', get_bukudb())
    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = request.args.get(
        get_per_page_parameter(),
        type=int,
        default=int(
            current_app.config.get('BUKUSERVER_PER_PAGE', views.DEFAULT_PER_PAGE))
    )
    url_render_mode = current_app.config['BUKUSERVER_URL_RENDER_MODE']
    create_bookmarks_form = forms.BookmarkForm()
    if request.method == 'GET':
        all_bookmarks = bukudb.get_rec_all()
        result = {
            'bookmarks': []
        }
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
        if request.path.startswith('/api/'):
            res = jsonify(result)
        else:
            if request.args.getlist('tag'):
                tags = request.args.getlist('tag')
                result['bookmarks'] = [
                    x for x in result['bookmarks']
                    if set(tags).issubset(set(x['tags']))
                ]
            current_app.logger.debug('total bookmarks:{}'.format(len(result['bookmarks'])))
            current_app.logger.debug('per page:{}'.format(per_page))
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
                result=result,
                pagination=pagination,
                search_bookmarks_form=forms.SearchBookmarksForm(),
                create_bookmarks_form=create_bookmarks_form,
                url_render_mode=url_render_mode,
            )
    elif request.method == 'POST':
        url_data = create_bookmarks_form.url.data
        result_flag = bukudb.add_rec(
            url_data,
            create_bookmarks_form.title.data,
            create_bookmarks_form.tags.data,
            create_bookmarks_form.description.data
        )
        if request.path.startswith('/api/'):
            res = [
                jsonify(response.response_template['success']), status.HTTP_200_OK,
                {'ContentType': 'application/json'}
            ] if result_flag != -1 else [
                jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST,
                {'ContentType': 'application/json'}
            ]
        else:
            bm_text = '[<a href="{0}">{0}</a>]'.format(url_data)
            if result_flag != -1:
                flash(Markup('Success creating bookmark {}.'.format(bm_text)), 'success')
            else:
                flash(Markup('Failed creating bookmark {}.'.format(bm_text)), 'danger')
            return redirect(url_for('bookmarks-html'))
    elif request.method == 'DELETE':
        result_flag = bukudb.cleardb()
        res = [
            jsonify(response.response_template['success']), status.HTTP_200_OK,
            {'ContentType': 'application/json'}
        ] if result_flag else [
            jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST,
            {'ContentType': 'application/json'}
        ]
    return res


def refresh_bookmarks():
    res = None
    if request.method == 'POST':
        print(request.form['index'])
        print(request.form['threads'])
        result_flag = getattr(
            flask.g,
            'bukudb',
            get_bukudb()).refreshdb(request.form['index'], request.form['threads'])
        if result_flag:
            res = (jsonify(response.response_template['success']),
                   status.HTTP_200_OK,
                   {'ContentType': 'application/json'})
        else:
            res = (jsonify(response.response_template['failure']),
                   status.HTTP_400_BAD_REQUEST,
                   {'ContentType': 'application/json'})
    return res


def bookmark_api(id):
    res = None
    try:
        id = int(id)
    except ValueError:
        return jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, \
               {'ContentType': 'application/json'}
    bukudb = getattr(flask.g, 'bukudb', get_bukudb())
    bookmark_form = forms.BookmarkForm()
    is_html_post_request = request.method == 'POST' and not request.path.startswith('/api/')
    if request.method == 'GET':
        bookmark = bukudb.get_rec_by_id(id)
        if bookmark is not None:
            result = {
                'url': bookmark[1],
                'title': bookmark[2],
                'tags': list([_f for _f in bookmark[3].split(',') if _f]),
                'description': bookmark[4]
            }
            if request.path.startswith('/api/'):
                res = jsonify(result)
            else:
                bookmark_form.url.data = result['url']
                bookmark_form.title.data = result['title']
                bookmark_form.tags.data = bookmark[3]
                bookmark_form.description.data = result['description']
                res = render_template(
                    'bukuserver/bookmark_edit.html',
                    result=result,
                    bookmark_form=bookmark_form,
                    bookmark_id=bookmark[0]
                )
        else:
            res = jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, \
                   {'ContentType': 'application/json'}
    elif request.method == 'PUT' or is_html_post_request:
        if request.method == 'PUT':
            result_flag = bukudb.update_rec(
                id,
                request.form['url'],
                request.form.get('title'),
                request.form['tags'],
                request.form['description'])
            if result_flag and not is_html_post_request:
                res = (jsonify(response.response_template['success']),
                       status.HTTP_200_OK,
                       {'ContentType': 'application/json'})
            elif not result_flag and not is_html_post_request:
                res = (jsonify(response.response_template['failure']),
                       status.HTTP_400_BAD_REQUEST,
                       {'ContentType': 'application/json'})
        elif is_html_post_request:
            result_flag = bukudb.update_rec(
                id,
                bookmark_form.url.data,
                bookmark_form.title.data,
                bookmark_form.tags.data,
                bookmark_form.description.data)
            if result_flag:
                flash(Markup('Success edit bookmark, id:{}'.format(id)), 'success')
            else:
                flash(Markup('Failed edit bookmark, id:{}'.format(id)), 'danger')
            res = redirect(url_for('bookmarks-html'))
        else:
            abort(400, description="Unknown Condition")
    else:
        result_flag = bukudb.delete_rec(id)
        if result_flag:
            res = (jsonify(response.response_template['success']),
                   status.HTTP_200_OK,
                   {'ContentType': 'application/json'})
        else:
            res = (jsonify(response.response_template['failure']),
                   status.HTTP_400_BAD_REQUEST,
                   {'ContentType': 'application/json'})
    return res


def refresh_bookmark(id):
    try:
        id = int(id)
    except ValueError:
        return jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, \
               {'ContentType': 'application/json'}
    res = None
    if request.method == 'POST':
        result_flag = getattr(flask.g, 'bukudb',
                              get_bukudb()).refreshdb(id, request.form['threads'])
        if result_flag:
            res = (jsonify(response.response_template['success']),
                   status.HTTP_200_OK,
                   {'ContentType': 'application/json'})
        else:
            res = (jsonify(response.response_template['failure']),
                   status.HTTP_400_BAD_REQUEST,
                   {'ContentType': 'application/json'})
    return res


def get_tiny_url(id):
    try:
        id = int(id)
    except ValueError:
        return jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, \
               {'ContentType': 'application/json'}
    res = None
    if request.method == 'GET':
        shortened_url = getattr(flask.g, 'bukudb', get_bukudb()).tnyfy_url(id)
        if shortened_url is not None:
            result = {
                'url': shortened_url
            }
            res = jsonify(result)
        else:
            res = (jsonify(response.response_template['failure']),
                   status.HTTP_400_BAD_REQUEST,
                   {'ContentType': 'application/json'})
    return res


def get_long_url(id):
    try:
        id = int(id)
    except ValueError:
        return jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, \
               {'ContentType': 'application/json'}

    res = None
    if request.method == 'GET':
        bookmark = getattr(flask.g, 'bukudb', get_bukudb()).get_rec_by_id(id)
        if bookmark is not None:
            result = {
                'url': bookmark[1],
            }
            res = jsonify(result)
        else:
            res = (jsonify(response.response_template['failure']),
                   status.HTTP_400_BAD_REQUEST,
                   {'ContentType': 'application/json'})
    return res


def bookmark_range_operations(starting_id, ending_id):

    try:
        starting_id = int(starting_id)
        ending_id = int(ending_id)
    except ValueError:
        return jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, \
               {'ContentType': 'application/json'}
    res = None
    bukudb = getattr(flask.g, 'bukudb', get_bukudb())
    max_id = bukudb.get_max_id()
    if starting_id > max_id or ending_id > max_id:
        return jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, \
               {'ContentType': 'application/json'}

    if request.method == 'GET':
        result = {
            'bookmarks': {}
        }
        for i in range(starting_id, ending_id + 1, 1):
            bookmark = bukudb.get_rec_by_id(i)
            result['bookmarks'][i] = {
                'url': bookmark[1],
                'title': bookmark[2],
                'tags': list([_f for _f in bookmark[3].split(',') if _f]),
                'description': bookmark[4]
            }
        res = jsonify(result)
    elif request.method == 'DELETE':
        for i in range(starting_id, ending_id + 1, 1):
            result_flag = bukudb.delete_rec(i)
            if result_flag is False:
                return (jsonify(response.response_template['failure']),
                        status.HTTP_400_BAD_REQUEST,
                        {'ContentType': 'application/json'})
        res = (jsonify(response.response_template['success']),
               status.HTTP_200_OK,
               {'ContentType': 'application/json'})
    elif request.method == 'PUT':
        for i in range(starting_id, ending_id + 1, 1):
            updated_bookmark = request.form[str(i)]
            result_flag = bukudb.update_rec(
                i,
                updated_bookmark['url'],
                updated_bookmark['title'],
                updated_bookmark['tags'],
                updated_bookmark['description'])

            if result_flag is False:
                return (jsonify(response.response_template['failure']),
                        status.HTTP_400_BAD_REQUEST,
                        {'ContentType': 'application/json'})
        res = jsonify(response.response_template['success']), status.HTTP_200_OK, \
               {'ContentType': 'application/json'}
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
        if bookmarks is not None:
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


def create_app(config_filename=None):
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
    app.config['BUKUSERVER_DB_FILE'] = os.getenv('BUKUSERVER_DB_FILE')
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
        app, name='Buku Server', template_mode='bootstrap3',
        index_view=views.CustomAdminIndexView(
            template='bukuserver/home.html', url='/'
        )
    )
    # routing
    #  api
    app.add_url_rule('/api/tags', 'get_tags', tag_list, methods=['GET'])
    app.add_url_rule('/api/tags/<tag>', 'update_tag', tag_detail, methods=['GET', 'PUT'])
    app.add_url_rule(
        '/api/network_handle',
        'networkk_handle',
        network_handle_detail,
        methods=['POST'])
    app.add_url_rule('/api/bookmarks', 'bookmarks', bookmarks, methods=['GET', 'POST', 'DELETE'])
    app.add_url_rule(
        '/api/bookmarks/refresh',
        'refresh_bookmarks',
        refresh_bookmarks,
        methods=['POST'])
    app.add_url_rule(
        '/api/bookmarks/<id>',
        'bookmark_api',
        bookmark_api,
        methods=['GET', 'PUT', 'DELETE'])
    app.add_url_rule(
        '/api/bookmarks/<id>/refresh',
        'refresh_bookmark',
        refresh_bookmark,
        methods=['POST'])
    app.add_url_rule('/api/bookmarks/<id>/tiny', 'get_tiny_url', get_tiny_url, methods=['GET'])
    app.add_url_rule('/api/bookmarks/<id>/long', 'get_long_url', get_long_url, methods=['GET'])
    app.add_url_rule(
        '/api/bookmarks/<starting_id>/<ending_id>',
        'bookmark_range_operations', bookmark_range_operations, methods=['GET', 'PUT', 'DELETE'])
    app.add_url_rule(
        '/api/bookmarks/search',
        'search_bookmarks',
        search_bookmarks,
        methods=['GET', 'DELETE'])
    #  non api
    admin.add_view(views.BookmarkModelView(
        bukudb, 'Bookmarks', page_size=per_page, url_render_mode=url_render_mode))
    admin.add_view(views.TagModelView(
        bukudb, 'Tags', page_size=per_page))
    admin.add_view(views.StatisticView(
        bukudb, 'Statistic', endpoint='statistic'))
    return app


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
        'app_name': 'Buku',
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
