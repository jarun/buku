#!/usr/bin/env python
# pylint: disable=wrong-import-order, ungrouped-imports
"""Server module."""
import os

from buku import BukuDb
from flask.cli import FlaskGroup
from flask_api import status
from flask_bootstrap import Bootstrap
from flask_paginate import Pagination, get_page_parameter, get_per_page_parameter
from markupsafe import Markup
import click
import flask
from flask import (
    current_app,
    flash,
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

try:
    from . import response, forms
except ImportError:
    from bukuserver import response, forms


DEFAULT_PER_PAGE = 10

def get_tags():
    """get tags."""
    tags = getattr(flask.g, 'bukudb', BukuDb()).get_tag_all()
    result = {
        'tags': tags[0]
    }
    if request.path.startswith('/api/'):
        res = jsonify(result)
    else:
        res = render_template('bukuserver/tags.html', result=result)
    return res


def update_tag(tag):
    res = None
    if request.method == 'PUT':
        result_flag = getattr(flask.g, 'bukudb', BukuDb()).replace_tag(tag, request.form.getlist('tags'))
        if result_flag:
            res = jsonify(response.response_template['success']), status.HTTP_200_OK, {'ContentType': 'application/json'}
        else:
            res = jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, {'ContentType': 'application/json'}
    return res


def chunks(l, n):
    n = max(1, n)
    return (l[i:i+n] for i in range(0, len(l), n))


def bookmarks():
    """Bookmarks."""
    res = None
    bukudb = getattr(flask.g, 'bukudb', BukuDb())
    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = request.args.get(
        get_per_page_parameter(),
        type=int,
        default=int(
            current_app.config.get('BUKUSERVER_PER_PAGE', DEFAULT_PER_PAGE))
    )
    create_bookmarks_form = forms.CreateBookmarksForm()
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
            bms = list(chunks(result['bookmarks'], per_page))
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
        result_flag = getattr(flask.g, 'bukudb', BukuDb()).refreshdb(request.form['index'], request.form['threads'])
        if result_flag:
            res = jsonify(response.response_template['success']), status.HTTP_200_OK, {'ContentType': 'application/json'}
        else:
            res = jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, {'ContentType': 'application/json'}
    return res


def bookmark_api(id):
    res = None
    try:
        id = int(id)
    except ValueError:
        return jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, \
               {'ContentType': 'application/json'}
    bukudb = getattr(flask.g, 'bukudb', BukuDb())
    if request.method == 'GET':
        bookmark = bukudb.get_rec_by_id(id)
        if bookmark is not None:
            result = {
                'url': bookmark[1],
                'title': bookmark[2],
                'tags': list([_f for _f in bookmark[3].split(',') if _f]),
                'description': bookmark[4]
            }
            return jsonify(result)
        else:
            return jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, \
                   {'ContentType': 'application/json'}
    elif request.method == 'PUT':
        result_flag = bukudb.update_rec(
            id, request.form['url'], request.form.get('title'), request.form['tags'], request.form['description'])
        if result_flag:
            res = jsonify(response.response_template['success']), status.HTTP_200_OK, {'ContentType': 'application/json'}
        else:
            res = jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, {'ContentType': 'application/json'}

    else:
        result_flag = bukudb.delete_rec(id)
        if result_flag:
            res = jsonify(response.response_template['success']), status.HTTP_200_OK, {'ContentType': 'application/json'}
        else:
            res = jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, {'ContentType': 'application/json'}
    return res


def refresh_bookmark(id):
    try:
        id = int(id)
    except ValueError:
        return jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, \
               {'ContentType': 'application/json'}
    res = None
    if request.method == 'POST':
        result_flag = getattr(flask.g, 'bukudb', BukuDb()).refreshdb(id, request.form['threads'])
        if result_flag:
            res = jsonify(response.response_template['success']), status.HTTP_200_OK, {'ContentType': 'application/json'}
        else:
            res = jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, {'ContentType': 'application/json'}
    return res


def get_tiny_url(id):
    try:
        id = int(id)
    except ValueError:
        return jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, \
               {'ContentType': 'application/json'}
    res = None
    if request.method == 'GET':
        shortened_url = getattr(flask.g, 'bukudb', BukuDb()).tnyfy_url(id)
        if shortened_url is not None:
            result = {
                'url': shortened_url
            }
            res = jsonify(result)
        else:
            res = jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, {'ContentType': 'application/json'}
    return res


def get_long_url(id):
    try:
        id = int(id)
    except ValueError:
        return jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, \
               {'ContentType': 'application/json'}

    res = None
    if request.method == 'GET':
        bookmark = getattr(flask.g, 'bukudb', BukuDb()).get_rec_by_id(id)
        if bookmark is not None:
            result = {
                'url': bookmark[1],
            }
            res = jsonify(result)
        else:
            res = jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, {'ContentType': 'application/json'}
    return res


def bookmark_range_operations(starting_id, ending_id):

    try:
        starting_id = int(starting_id)
        ending_id = int(ending_id)
    except ValueError:
        return jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, \
               {'ContentType': 'application/json'}
    res = None
    bukudb = getattr(flask.g, 'bukudb', BukuDb())
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
                return jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, \
                       {'ContentType': 'application/json'}
        res = jsonify(response.response_template['success']), status.HTTP_200_OK, {'ContentType': 'application/json'}
    elif request.method == 'PUT':
        for i in range(starting_id, ending_id + 1, 1):
            updated_bookmark = request.form[str(i)]
            result_flag = bukudb.update_rec(
                i, updated_bookmark['url'], updated_bookmark['title'], updated_bookmark['tags'], updated_bookmark['description'])

            if result_flag is False:
                return jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, \
                       {'ContentType': 'application/json'}
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
        all_keywords = \
            all_keywords if type(all_keywords) == bool else all_keywords.lower() == 'true'
        deep = \
            deep if type(deep) == bool else deep.lower() == 'true'
        regex = \
            regex if type(regex) == bool else regex.lower() == 'true'
    else:
        keywords = search_bookmarks_form.keywords.data
        all_keywords = search_bookmarks_form.all_keywords.data
        deep = search_bookmarks_form.deep.data
        regex = search_bookmarks_form.regex.data

    result = {'bookmarks': []}
    bukudb = getattr(flask.g, 'bukudb', BukuDb())
    found_bookmarks = bukudb.searchdb(keywords, all_keywords, deep, regex)
    found_bookmarks = [] if found_bookmarks is None else found_bookmarks
    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = request.args.get(
        get_per_page_parameter(),
        type=int,
        default=int(
            current_app.config.get('BUKUSERVER_PER_PAGE', DEFAULT_PER_PAGE))
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
            bms = list(chunks(result['bookmarks'], per_page))
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
                search_bookmarks_form=search_bookmarks_form)
    elif request.method == 'DELETE':
        if found_bookmarks is not None:
            for bookmark in found_bookmarks:
                result_flag = bukudb.delete_rec(bookmark[0])
                if result_flag is False:
                    res = jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, {'ContentType': 'application/json'}
        if res is None:
            res = jsonify(response.response_template['success']), status.HTTP_200_OK, {'ContentType': 'application/json'}
    return res


def create_app(config_filename=None):
    """create app."""
    app = Flask(__name__)
    app.config['BUKUSERVER_PER_PAGE'] = os.getenv(
        'BUKUSERVER_PER_PAGE', DEFAULT_PER_PAGE)
    app.config['SECRET_KEY'] = os.getenv('BUKUSERVER_SERVER_SECRET_KEY') or os.urandom(24)
    bukudb = BukuDb()
    app.app_context().push()
    setattr(flask.g, 'bukudb', bukudb)

    @app.shell_context_processor
    def shell_context():
        """Shell context definition."""
        return {'app': app, 'bukudb': bukudb}

    Bootstrap(app)
    # routing
    app.add_url_rule('/api/tags', 'get_tags', get_tags, methods=['GET'])
    app.add_url_rule('/tags', 'get_tags-html', get_tags, methods=['GET'])
    app.add_url_rule('/api/tags/<tag>', 'update_tag', update_tag, methods=['PUT'])
    app.add_url_rule('/api/bookmarks', 'bookmarks', bookmarks, methods=['GET', 'POST', 'DELETE'])
    app.add_url_rule('/bookmarks', 'bookmarks-html', bookmarks, methods=['GET', 'POST', 'DELETE'])
    app.add_url_rule('/api/bookmarks/refresh', 'refresh_bookmarks', refresh_bookmarks, methods=['POST'])
    app.add_url_rule('/api/bookmarks/<id>', 'bookmark_api', bookmark_api, methods=['GET', 'PUT', 'DELETE'])
    app.add_url_rule('/api/bookmarks/<id>/refresh', 'refresh_bookmark', refresh_bookmark, methods=['POST'])
    app.add_url_rule('/api/bookmarks/<id>/tiny', 'get_tiny_url', get_tiny_url, methods=['GET'])
    app.add_url_rule('/api/bookmarks/<id>/long', 'get_long_url', get_long_url, methods=['GET'])
    app.add_url_rule(
        '/api/bookmarks/<starting_id>/<ending_id>',
        'bookmark_range_operations', bookmark_range_operations, methods=['GET', 'PUT', 'DELETE'])
    app.add_url_rule('/api/bookmarks/search', 'search_bookmarks', search_bookmarks, methods=['GET', 'DELETE'])
    app.add_url_rule('/bookmarks/search', 'search_bookmarks-html', search_bookmarks, methods=['GET'])
    app.add_url_rule('/', 'index', lambda: render_template(
        'bukuserver/index.html', search_bookmarks_form=forms.SearchBookmarksForm()))
    return app


@click.group(cls=FlaskGroup, create_app=create_app)
def cli():
    """This is a management script for the wiki application."""


if __name__ == '__main__':
    cli()
