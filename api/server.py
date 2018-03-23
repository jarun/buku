#!/usr/bin/env python
from buku import BukuDb
from flask import Flask, jsonify, request
from flask.cli import FlaskGroup
from flask_api import status
import click
import response
import flask


def get_tags():
    tags = getattr(flask.g, 'bukudb').get_tag_all()
    result = {
        'tags': tags[0]
    }
    return jsonify(result)


def update_tag(tag):
    if request.method == 'PUT':
        result_flag = getattr(flask.g, 'bukudb').replace_tag(tag, request.form.getlist('tags'))
        if result_flag:
            return jsonify(response.response_template['success']), status.HTTP_200_OK, \
                   {'ContentType': 'application/json'}
        else:
            return jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, \
                   {'ContentType': 'application/json'}


def bookmarks():
    if request.method == 'GET':
        all_bookmarks = getattr(flask.g, 'bukudb').get_rec_all()
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
        return jsonify(result)
    elif request.method == 'POST':
        result_flag = getattr(flask.g, 'bukudb').add_rec(request.form['url'], request.form['title'],
                                     request.form['tags'], request.form['description'])
        if result_flag:
            return jsonify(response.response_template['success']), status.HTTP_200_OK, \
                   {'ContentType': 'application/json'}
        else:
            return jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, \
                   {'ContentType': 'application/json'}
    elif request.method == 'DELETE':
        result_flag = getattr(flask.g, 'bukudb').cleardb()
        if result_flag:
            return jsonify(response.response_template['success']), status.HTTP_200_OK, \
                   {'ContentType': 'application/json'}
        else:
            return jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, \
                   {'ContentType': 'application/json'}


def refresh_bookmarks():
    if request.method == 'POST':
        print(request.form['index'])
        print(request.form['threads'])
        result_flag = getattr(flask.g, 'bukudb').refreshdb(request.form['index'], request.form['threads'])
        if result_flag:
            return jsonify(response.response_template['success']), status.HTTP_200_OK, \
                   {'ContentType': 'application/json'}
        else:
            return jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, \
                   {'ContentType': 'application/json'}


def bookmark_api(id):
    try:
        id = int(id)
    except ValueError:
        return jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, \
               {'ContentType': 'application/json'}
    if request.method == 'GET':
        bookmark = getattr(flask.g, 'bukudb').get_rec_by_id(id)
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
        result_flag = getattr(flask.g, 'bukudb').update_rec(id, request.form['url'], request.form.get('title'),
                                        request.form['tags'], request.form['description'])
        if result_flag:
            return jsonify(response.response_template['success']), status.HTTP_200_OK, \
                   {'ContentType': 'application/json'}
        else:
            return jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, \
                   {'ContentType': 'application/json'}
    else:
        result_flag = getattr(flask.g, 'bukudb').delete_rec(id)
        if result_flag:
            return jsonify(response.response_template['success']), status.HTTP_200_OK, \
                   {'ContentType': 'application/json'}
        else:
            return jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, \
                   {'ContentType': 'application/json'}


def refresh_bookmark(id):
    try:
        id = int(id)
    except ValueError:
        return jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, \
               {'ContentType': 'application/json'}
    if request.method == 'POST':
        result_flag = getattr(flask.g, 'bukudb').refreshdb(id, request.form['threads'])
        if result_flag:
            return jsonify(response.response_template['success']), status.HTTP_200_OK, \
                   {'ContentType': 'application/json'}
        else:
            return jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, \
                   {'ContentType': 'application/json'}


def get_tiny_url(id):
    try:
        id = int(id)
    except ValueError:
        return jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, \
               {'ContentType': 'application/json'}

    if request.method == 'GET':
        shortened_url = getattr(flask.g, 'bukudb').tnyfy_url(id)
        if shortened_url is not None:
            result = {
                'url': shortened_url
            }
            return jsonify(result)
        else:
            return jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, \
                   {'ContentType': 'application/json'}


def get_long_url(id):
    try:
        id = int(id)
    except ValueError:
        return jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, \
               {'ContentType': 'application/json'}

    if request.method == 'GET':
        bookmark = getattr(flask.g, 'bukudb').get_rec_by_id(id)
        if bookmark is not None:
            result = {
                'url': bookmark[1],
            }
            return jsonify(result)
        else:
            return jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, \
                   {'ContentType': 'application/json'}


def bookmark_range_operations(starting_id, ending_id):

    try:
        starting_id = int(starting_id)
        ending_id = int(ending_id)
    except ValueError:
        return jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, \
               {'ContentType': 'application/json'}

    max_id = getattr(flask.g, 'bukudb').get_max_id()
    if starting_id > max_id or ending_id > max_id:
        return jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, \
               {'ContentType': 'application/json'}

    if request.method == 'GET':
        result = {
            'bookmarks': {}
        }
        for i in range(starting_id, ending_id + 1, 1):
            bookmark = getattr(flask.g, 'bukudb').get_rec_by_id(i)
            bookmarks[i] = {
                'url': bookmark[1],
                'title': bookmark[2],
                'tags': list([_f for _f in bookmark[3].split(',') if _f]),
                'description': bookmark[4]
            }
        return jsonify(result)
    elif request.method == 'DELETE':
        for i in range(starting_id, ending_id + 1, 1):
            result_flag = getattr(flask.g, 'bukudb').delete_rec(i)
            if result_flag is False:
                return jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, \
                       {'ContentType': 'application/json'}
        return jsonify(response.response_template['success']), status.HTTP_200_OK, \
               {'ContentType': 'application/json'}
    elif request.method == 'PUT':
        for i in range(starting_id, ending_id + 1, 1):
            updated_bookmark = request.form[str(i)]
            result_flag = getattr(flask.g, 'bukudb').update_rec(i, updated_bookmark['url'], updated_bookmark['title'],
                                            updated_bookmark['tags'], updated_bookmark['description'])

            if result_flag is False:
                return jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, \
                       {'ContentType': 'application/json'}
        return jsonify(response.response_template['success']), status.HTTP_200_OK, \
               {'ContentType': 'application/json'}


def search_bookmarks():
    keywords = request.form.getlist('keywords')
    all_keywords = request.form.get('all_keywords')
    deep = request.form.get('deep')
    regex = request.form.get('regex')
    all_keywords = False if all_keywords is None else all_keywords
    deep = False if deep is None else deep
    regex = False if regex is None else regex
    all_keywords = all_keywords if type(all_keywords) == bool else all_keywords.lower() == 'true'
    deep = deep if type(deep) == bool else deep.lower() == 'true'
    regex = regex if type(regex) == bool else regex.lower() == 'true'

    results = {'bookmarks': []}
    found_bookmarks = getattr(flask.g, 'bukudb').searchdb(keywords, all_keywords, deep, regex)

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
                results['bookmarks'].append(result_bookmark)
        return jsonify(results)
    elif request.method == 'DELETE':
        if found_bookmarks is not None:
            for bookmark in found_bookmarks:
                result_flag = getattr(flask.g, 'bukudb').delete_rec(bookmark[0])
                if result_flag is False:
                    return jsonify(response.response_template['failure']), status.HTTP_400_BAD_REQUEST, \
                           {'ContentType': 'application/json'}
        return jsonify(response.response_template['success']), status.HTTP_200_OK, \
               {'ContentType': 'application/json'}


def create_app(config_filename=None):
    """create app."""
    app = Flask(__name__)
    bukudb = BukuDb()
    setattr(flask.g, 'bukudb', bukudb)

    @app.shell_context_processor
    def shell_context():
        """Shell context definition."""
        return {'app': app, 'bukudb': bukudb}

    # routing
    app.add_url_rule('/api/tags', 'get_tags', get_tags, methods=['GET'])
    app.add_url_rule('/api/tags/<tag>', 'update_tag', update_tag, methods=['PUT'])
    app.add_url_rule('/api/bookmarks', 'bookmarks', bookmarks, methods=['GET', 'POST', 'DELETE'])
    app.add_url_rule('/api/bookmarks/refresh', 'refresh_bookmarks', refresh_bookmarks, methods=['POST'])
    app.add_url_rule('/api/bookmarks/<id>', 'bookmark_api', refresh_bookmarks, methods=['GET', 'PUT', 'DELETE'])
    app.add_url_rule('/api/bookmarks/<id>/refresh', 'refresh_bookmark', refresh_bookmark, methods=['POST'])
    app.add_url_rule('/api/bookmarks/<id>/tiny', 'get_tiny_url', get_tiny_url, methods=['GET'])
    app.add_url_rule('/api/bookmarks/<id>/long', 'get_long_url', get_long_url, methods=['GET'])
    app.add_url_rule('/api/bookmarks/<starting_id>/<ending_id>', 'bookmark_range_operations', bookmark_range_operations, methods=['GET', 'PUT', 'DELETE'])
    app.add_url_rule('/api/bookmarks/search', 'search_bookmarks', search_bookmarks, methods=['GET', 'DELETE'])
    return app


@click.group(cls=FlaskGroup, create_app=create_app)
def cli():
    """This is a management script for the wiki application."""


if __name__ == '__main__':
    cli()
