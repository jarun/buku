#!/usr/bin/env python
# pylint: disable=wrong-import-order, ungrouped-imports
"""Server module."""
import os
from collections import Counter
from urllib.parse import urlparse

from buku import BukuDb
from flask.cli import FlaskGroup
from flask_api import status
from flask_bootstrap import Bootstrap
from flask_paginate import Pagination, get_page_parameter, get_per_page_parameter
from markupsafe import Markup
import arrow
import click
import flask
from flask import (
    abort,
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
DEFAULT_URL_RENDER_MODE = 'full'
STATISTIC_DATA = None


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
    if request.method in ('PUT', 'POST'):
        new_tags = request.form.getlist('tags')
        result_flag = getattr(flask.g, 'bukudb', BukuDb()).replace_tag(tag, new_tags)
        op_text = 'replace tag [{}] with [{}]'.format(tag, ', '.join(new_tags))
        if request.method == 'PUT' and result_flag and request.path.startswith('/api/'):
            res = jsonify(response.response_template['success']), status.HTTP_200_OK, {'ContentType': 'application/json'}
        elif request.method == 'PUT' and request.path.startswith('/api/'):
            res = jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, {'ContentType': 'application/json'}
        elif request.method == 'POST' and result_flag:
            flash(Markup('Success {}'.format(op_text)), 'success')
            res = redirect(url_for('get_tags-html'))
        elif request.method == 'POST':
            flash(Markup('Failed {}'.format(op_text)), 'danger')
            res = redirect(url_for('get_tags-html'))
        else:
            abort(400, description="Unknown Condition")
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
    url_render_mode = current_app.config['BUKUSERVER_URL_RENDER_MODE']
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
    bookmark_form = forms.CreateBookmarksForm()
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
                id, request.form['url'], request.form.get('title'), request.form['tags'], request.form['description'])
            if result_flag and not is_html_post_request:
                res = jsonify(response.response_template['success']), status.HTTP_200_OK, {'ContentType': 'application/json'}
            elif not result_flag and not is_html_post_request:
                res = jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, {'ContentType': 'application/json'}
        elif is_html_post_request:
            result_flag = bukudb.update_rec(
                id, bookmark_form.url.data, bookmark_form.title.data, bookmark_form.tags.data, bookmark_form.description.data)
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
                search_bookmarks_form=search_bookmarks_form,
                create_bookmarks_form=forms.CreateBookmarksForm(),
            )
    elif request.method == 'DELETE':
        if found_bookmarks is not None:
            for bookmark in found_bookmarks:
                result_flag = bukudb.delete_rec(bookmark[0])
                if result_flag is False:
                    res = jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, {'ContentType': 'application/json'}
        if res is None:
            res = jsonify(response.response_template['success']), status.HTTP_200_OK, {'ContentType': 'application/json'}
    return res


def view_statistic():
    bukudb = getattr(flask.g, 'bukudb', BukuDb())
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

    return render_template(
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


def create_app(config_filename=None):
    """create app."""
    app = Flask(__name__)
    per_page = int(os.getenv('BUKUSERVER_PER_PAGE', DEFAULT_PER_PAGE))
    per_page = per_page if per_page > 0 else DEFAULT_PER_PAGE
    app.config['BUKUSERVER_PER_PAGE'] = per_page
    url_render_mode = os.getenv('BUKUSERVER_URL_RENDER_MODE', DEFAULT_URL_RENDER_MODE)
    if url_render_mode not in ('full', 'netloc'):
        url_render_mode = DEFAULT_URL_RENDER_MODE
    app.config['BUKUSERVER_URL_RENDER_MODE'] = url_render_mode
    app.config['SECRET_KEY'] = os.getenv('BUKUSERVER_SECRET_KEY') or os.urandom(24)
    bukudb = BukuDb()
    app.app_context().push()
    setattr(flask.g, 'bukudb', bukudb)

    @app.shell_context_processor
    def shell_context():
        """Shell context definition."""
        return {'app': app, 'bukudb': bukudb}

    app.jinja_env.filters['netloc'] = lambda x: urlparse(x).netloc  # pylint: disable=no-member

    Bootstrap(app)
    # routing
    app.add_url_rule('/api/tags', 'get_tags', get_tags, methods=['GET'])
    app.add_url_rule('/tags', 'get_tags-html', get_tags, methods=['GET'])
    app.add_url_rule('/api/tags/<tag>', 'update_tag', update_tag, methods=['PUT'])
    app.add_url_rule('/tags/<tag>', 'update_tag-html', update_tag, methods=['POST'])
    app.add_url_rule('/api/bookmarks', 'bookmarks', bookmarks, methods=['GET', 'POST', 'DELETE'])
    app.add_url_rule('/bookmarks', 'bookmarks-html', bookmarks, methods=['GET', 'POST', 'DELETE'])
    app.add_url_rule('/api/bookmarks/refresh', 'refresh_bookmarks', refresh_bookmarks, methods=['POST'])
    app.add_url_rule('/api/bookmarks/<id>', 'bookmark_api', bookmark_api, methods=['GET', 'PUT', 'DELETE'])
    app.add_url_rule('/bookmarks/<id>', 'bookmark_api-html', bookmark_api, methods=['GET', 'POST'])
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
    app.add_url_rule('/statistic', 'statistic', view_statistic, methods=['GET', 'POST'])
    return app


@click.group(cls=FlaskGroup, create_app=create_app)
def cli():
    """This is a management script for the wiki application."""


if __name__ == '__main__':
    cli()
