#!/usr/bin/env python
# pylint: disable=wrong-import-order, ungrouped-imports
"""Server module."""
import collections
import typing as T
from unittest import mock

from flask.views import MethodView
from flask_api import exceptions, status

import buku
from buku import BukuDb

import flask
from flask import current_app, jsonify, redirect, request, url_for

try:
    from . import forms, response
except ImportError:
    from bukuserver import forms, response


STATISTIC_DATA = None

response_ok = lambda: (jsonify(response.response_template['success']),
                       status.HTTP_200_OK,
                       {'ContentType': 'application/json'})
response_bad = lambda: (jsonify(response.response_template['failure']),
                        status.HTTP_400_BAD_REQUEST,
                        {'ContentType': 'application/json'})
to_response = lambda ok: response_ok() if ok else response_bad()

def entity(bookmark, id=False):
    data = {
        'id': bookmark.id,
        'url': bookmark.url,
        'title': bookmark.title,
        'tags': bookmark.taglist,
        'description': bookmark.desc,
    }
    if not id:
        data.pop('id')
    return data


def get_bukudb():
    """get bukudb instance"""
    db_file = current_app.config.get('BUKUSERVER_DB_FILE', None)
    return BukuDb(dbfile=db_file)


def search_tag(
    db: BukuDb, stag: T.Optional[str] = None, limit: T.Optional[int] = None
) -> T.Tuple[T.List[str], T.Dict[str, int]]:
    """search tag.

    db:
        buku db instance
    stag:
        search tag
    limit:
        positive integer limit

    Returns
    -------
    tuple
        list of unique tags sorted alphabetically and dictionary of tag and its usage count

    Raises
    ------
    ValueError
        if limit is not positive
    """
    if limit is not None and limit < 1:
        raise ValueError("limit must be positive")
    tags: T.Set[str] = set()
    counter = collections.Counter()
    query_list = ["SELECT DISTINCT tags , COUNT(tags) FROM bookmarks"]
    if stag:
        query_list.append("where tags LIKE :search_tag")
    query_list.append("GROUP BY tags")
    row: T.Tuple[str, int]
    for row in db.cur.execute(" ".join(query_list), {"search_tag": f"%{stag}%"}):
        for tag in row[0].strip(buku.DELIM).split(buku.DELIM):
            if not tag:
                continue
            tags.add(tag)
            counter[tag] += row[1]
    return list(sorted(tags)), dict(counter.most_common(limit))


class ApiTagView(MethodView):

    def get(self, tag: T.Optional[str]):
        bukudb = get_bukudb()
        if tag is None:
            return {"tags": search_tag(db=bukudb, limit=5)[0]}
        tags = search_tag(db=bukudb, stag=tag)
        if tag not in tags[1]:
            raise exceptions.NotFound()
        return {"name": tag, "usage_count": tags[1][tag]}

    def put(self, tag: str):
        bukudb = get_bukudb()
        try:
            new_tags = request.data.get('tags')  # type: ignore
            if new_tags:
                new_tags = new_tags.split(',')
            else:
                return response_bad()
        except AttributeError as e:
            raise exceptions.ParseError(detail=str(e))
        return to_response(bukudb.replace_tag(tag, new_tags))


class ApiBookmarkView(MethodView):

    def get(self, rec_id: T.Union[int, None]):
        if rec_id is None:
            bukudb = getattr(flask.g, 'bukudb', get_bukudb())
            all_bookmarks = bukudb.get_rec_all()
            result = {'bookmarks': [entity(bookmark, id=not request.path.startswith('/api/'))
                                    for bookmark in all_bookmarks]}
            res = jsonify(result)
        else:
            bukudb = getattr(flask.g, 'bukudb', get_bukudb())
            bookmark = bukudb.get_rec_by_id(rec_id)
            res = (response_bad() if bookmark is None else jsonify(entity(bookmark)))
        return res

    def post(self, rec_id: None = None):
        bukudb = getattr(flask.g, 'bukudb', get_bukudb())
        create_bookmarks_form = forms.ApiBookmarkForm()
        url_data = create_bookmarks_form.url.data
        result_flag = bukudb.add_rec(
            url_data,
            create_bookmarks_form.title.data,
            create_bookmarks_form.tags.data,
            create_bookmarks_form.description.data
        )
        return to_response(result_flag)

    def put(self, rec_id: int):
        bukudb = getattr(flask.g, 'bukudb', get_bukudb())
        result_flag = bukudb.update_rec(
            rec_id,
            request.form.get('url'),
            request.form.get('title'),
            request.form.get('tags'),
            request.form.get('description'))
        return to_response(result_flag)

    def delete(self, rec_id: T.Union[int, None]):
        if rec_id is None:
            bukudb = getattr(flask.g, 'bukudb', get_bukudb())
            with mock.patch('buku.read_in', return_value='y'):
                result_flag = bukudb.cleardb()
        else:
            bukudb = getattr(flask.g, 'bukudb', get_bukudb())
            result_flag = bukudb.delete_rec(rec_id)
        return to_response(result_flag)


class ApiBookmarkRangeView(MethodView):

    def get(self, starting_id: int, ending_id: int):
        bukudb = getattr(flask.g, 'bukudb', get_bukudb())
        max_id = bukudb.get_max_id() or 0
        if starting_id > max_id or ending_id > max_id:
            return response_bad()
        result = {'bookmarks': {i: entity(bukudb.get_rec_by_id(i))
                                for i in range(starting_id, ending_id + 1)}}
        return jsonify(result)

    def put(self, starting_id: int, ending_id: int):
        bukudb = getattr(flask.g, 'bukudb', get_bukudb())
        max_id = bukudb.get_max_id() or 0
        if starting_id > max_id or ending_id > max_id:
            return response_bad()
        for i in range(starting_id, ending_id + 1, 1):
            updated_bookmark = request.data.get(str(i))  # type: ignore
            result_flag = bukudb.update_rec(
                i,
                updated_bookmark.get('url'),
                updated_bookmark.get('title'),
                updated_bookmark.get('tags'),
                updated_bookmark.get('description'))
            if result_flag is False:
                return response_bad()
        return response_ok()

    def delete(self, starting_id: int, ending_id: int):
        bukudb = getattr(flask.g, 'bukudb', get_bukudb())
        max_id = bukudb.get_max_id() or 0
        if starting_id > max_id or ending_id > max_id:
            return response_bad()
        idx = min([starting_id, ending_id])
        result_flag = bukudb.delete_rec(idx, starting_id, ending_id, is_range=True)
        return to_response(result_flag)


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

        bukudb = getattr(flask.g, 'bukudb', get_bukudb())
        res = None
        result = {'bookmarks': [entity(bookmark, id=True)
                                for bookmark in bukudb.searchdb(keywords, all_keywords, deep, regex)]}
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
        res = None
        for bookmark in bukudb.searchdb(keywords, all_keywords, deep, regex):
            if not bukudb.delete_rec(bookmark.id):
                res = response_bad()
        return res or response_ok()


class BookmarkletView(MethodView):  # pylint: disable=too-few-public-methods
    def get(self):
        url = request.args.get('url')
        title = request.args.get('title')
        description = request.args.get('description')

        bukudb = getattr(flask.g, 'bukudb', get_bukudb())
        rec_id = bukudb.get_rec_id(url)
        if rec_id:
            return redirect(url_for('bookmark.edit_view', id=rec_id))
        return redirect(url_for('bookmark.create_view', link=url, title=title, description=description))
