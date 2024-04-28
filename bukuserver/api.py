#!/usr/bin/env python
# pylint: disable=wrong-import-order, ungrouped-imports
"""Server module."""
import collections
import typing as T
from unittest import mock

from flask.views import MethodView

import buku
from buku import BukuDb

import flask
from flask import current_app, redirect, request, url_for

try:
    from response import Response
    from forms import ApiBookmarkCreateForm, ApiBookmarkEditForm, ApiBookmarkRangeEditForm, ApiTagForm
except ImportError:
    from bukuserver.response import Response
    from bukuserver.forms import ApiBookmarkCreateForm, ApiBookmarkEditForm, ApiBookmarkRangeEditForm, ApiTagForm


STATISTIC_DATA = None


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
            return Response.SUCCESS(data={"tags": search_tag(db=bukudb, limit=5)[0]})
        tags = search_tag(db=bukudb, stag=tag)
        if tag not in tags[1]:
            return Response.TAG_NOT_FOUND()
        return Response.SUCCESS(data={"name": tag, "usage_count": tags[1][tag]})

    def put(self, tag: str):
        form = ApiTagForm({})
        error_response, data = form.process_data(request.get_json())
        if error_response is not None:
            return error_response(data=data)
        bukudb = get_bukudb()
        tags = search_tag(db=bukudb, stag=tag)
        if tag not in tags[1]:
            return Response.TAG_NOT_FOUND()
        try:
            bukudb.replace_tag(tag, form.tags.data)
            return Response.SUCCESS()
        except (ValueError, RuntimeError):
            return Response.FAILURE()

    def delete(self, tag: str):
        if buku.DELIM in tag:
            return Response.TAG_NOT_VALID()
        bukudb = get_bukudb()
        tags = search_tag(db=bukudb, stag=tag)
        if tag not in tags[1]:
            return Response.TAG_NOT_FOUND()
        return Response.from_flag(bukudb.delete_tag_at_index(0, tag, chatty=False))


class ApiBookmarkView(MethodView):

    def get(self, rec_id: T.Union[int, None]):
        if rec_id is None:
            bukudb = getattr(flask.g, 'bukudb', get_bukudb())
            all_bookmarks = bukudb.get_rec_all()
            result = {'bookmarks': [entity(bookmark, id=not request.path.startswith('/api/'))
                                    for bookmark in all_bookmarks]}
        else:
            bukudb = getattr(flask.g, 'bukudb', get_bukudb())
            bookmark = bukudb.get_rec_by_id(rec_id)
            if bookmark is None:
                return Response.BOOKMARK_NOT_FOUND()
            result = entity(bookmark)
        return Response.SUCCESS(data=result)

    def post(self, rec_id: None = None):
        form = ApiBookmarkCreateForm({})
        error_response, error_data = form.process_data(request.get_json())
        if error_response is not None:
            return error_response(data=error_data)
        bukudb = getattr(flask.g, 'bukudb', get_bukudb())
        result_flag = bukudb.add_rec(
            form.url.data,
            form.title.data,
            form.tags_str,
            form.description.data,
            fetch=form.fetch.data)
        return Response.from_flag(result_flag)

    def put(self, rec_id: int):
        form = ApiBookmarkEditForm({})
        error_response, error_data = form.process_data(request.get_json())
        if error_response is not None:
            return error_response(data=error_data)
        bukudb = getattr(flask.g, 'bukudb', get_bukudb())
        result_flag = bukudb.update_rec(
            rec_id,
            form.url.data,
            form.title.data,
            form.tags_str,
            form.description.data)
        return Response.from_flag(result_flag)

    def delete(self, rec_id: T.Union[int, None]):
        if rec_id is None:
            bukudb = getattr(flask.g, 'bukudb', get_bukudb())
            with mock.patch('buku.read_in', return_value='y'):
                result_flag = bukudb.cleardb()
        else:
            bukudb = getattr(flask.g, 'bukudb', get_bukudb())
            result_flag = bukudb.delete_rec(rec_id)
        return Response.from_flag(result_flag)


class ApiBookmarkRangeView(MethodView):

    def get(self, starting_id: int, ending_id: int):
        bukudb = getattr(flask.g, 'bukudb', get_bukudb())
        max_id = bukudb.get_max_id() or 0
        if starting_id > ending_id or ending_id > max_id:
            return Response.RANGE_NOT_VALID()
        result = {'bookmarks': {i: entity(bukudb.get_rec_by_id(i))
                                for i in range(starting_id, ending_id + 1)}}
        return Response.SUCCESS(data=result)

    def put(self, starting_id: int, ending_id: int):
        bukudb = getattr(flask.g, 'bukudb', get_bukudb())
        max_id = bukudb.get_max_id() or 0
        if starting_id > ending_id or ending_id > max_id:
            return Response.RANGE_NOT_VALID()
        updates = []
        errors = {}
        for rec_id in range(starting_id, ending_id + 1):
            json = request.get_json().get(str(rec_id))
            if json is None:
                errors[rec_id] = 'Input required.'
                continue
            form = ApiBookmarkRangeEditForm({})
            error_response, error_data = form.process_data(json)
            if error_response is not None:
                errors[rec_id] = error_data.get('errors')
            updates += [{'index': rec_id,
                         'url': form.url.data,
                         'title_in': form.title.data,
                         'tags_in': form.tags_in,
                         'desc': form.description.data}]

        if errors:
            return Response.INPUT_NOT_VALID(data={'errors': errors})
        for update in updates:
            if not bukudb.update_rec(**update):
                return Response.FAILURE()
        return Response.SUCCESS()

    def delete(self, starting_id: int, ending_id: int):
        bukudb = getattr(flask.g, 'bukudb', get_bukudb())
        max_id = bukudb.get_max_id() or 0
        if starting_id > ending_id or ending_id > max_id:
            return Response.RANGE_NOT_VALID()
        idx = min([starting_id, ending_id])
        result_flag = bukudb.delete_rec(idx, starting_id, ending_id, is_range=True)
        return Response.from_flag(result_flag)


class ApiBookmarkSearchView(MethodView):

    def get(self):
        arg_obj = request.args
        keywords = arg_obj.getlist('keywords')  # pylint: disable=E1101
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
        result = {'bookmarks': [entity(bookmark, id=True)
                                for bookmark in bukudb.searchdb(keywords, all_keywords, deep, regex)]}
        current_app.logger.debug('total bookmarks:{}'.format(len(result['bookmarks'])))
        return Response.SUCCESS(data=result)

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
                res = Response.FAILURE()
        return res or Response.SUCCESS()


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
