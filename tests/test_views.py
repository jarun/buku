import logging
from argparse import Namespace

import pytest
from flask import current_app, request

from buku import BukuDb
from bukuserver import server
from bukuserver.views import BookmarkModelView, TagModelView


@pytest.fixture
def client(tmp_path):
    test_db = tmp_path / 'test.db'
    app = server.create_app(test_db.as_posix())
    app_context = app.test_request_context()
    app_context.push()
    client = app.test_client()
    return client


@pytest.mark.parametrize('disable_favicon', [False, True])
def test_bookmark_model_view(tmp_path, client, disable_favicon):
    logging.debug('client: %s', client)
    test_db = tmp_path / 'test.db'
    bukudb = BukuDb(dbfile=test_db.as_posix())
    inst = BookmarkModelView(bukudb)
    model = Namespace(
        description='randomdesc', id=1, tags='tags1',
        title='Example Domain', url='http://example.com')
    current_app.config['BUKUSERVER_DISABLE_FAVICON'] = disable_favicon
    assert inst._list_entry(None, model, 'Entry')


@pytest.fixture
def tmv_instance(tmp_path):
    """define tag model view instance"""
    test_db = tmp_path / 'test.db'
    bukudb = BukuDb(dbfile=test_db.as_posix())
    inst = TagModelView(bukudb)
    return inst


def test_tag_model_view_get_list_empty_db(tmv_instance):
    res = tmv_instance.get_list(None, None, None, None, [])
    assert res == (0, [])


@pytest.mark.parametrize(
    "sort_field, sort_desc, filters, exp_res",
    [
        [None, False, [], (0, [])],
        [None, False, [(0, "name", "t2")], (0, [])],
        ["name", False, [], (0, [])],
        ["name", True, [], (0, [])],
        ["usage_count", True, [], (0, [])],
    ],
)
def test_tag_model_view_get_list(tmv_instance, sort_field, sort_desc, filters, exp_res):
    tmv_instance.bukudb.add_rec('http://example.com/1.jpg', tags_in='t1,t2,t3')
    tmv_instance.bukudb.add_rec('http://example.com/2.jpg', tags_in='t2,t3')
    tmv_instance.bukudb.add_rec('http://example.com/3.jpg', tags_in='t3')
    res = tmv_instance.get_list(0, sort_field, sort_desc, None, filters)
    assert res == exp_res


@pytest.fixture
def bmv_instance(tmp_path):
    """define tag model view instance"""
    test_db = tmp_path / 'test.db'
    bukudb = BukuDb(dbfile=test_db.as_posix())
    inst = BookmarkModelView(bukudb)
    return inst


@pytest.mark.parametrize('url, exp_url', [
    ['http://example.com', 'http://example.com'],
    ['/bookmark/', None],
])
def test_bmv_create_form(bmv_instance, url, exp_url):
    request.args = {'url': url}
    form = bmv_instance.create_form()
    assert form.url.data == exp_url
