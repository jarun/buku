"""test for views.

resources: https://flask.palletsprojects.com/en/2.2.x/testing/
"""
from argparse import Namespace

import pytest
from flask import request

from buku import BukuDb
from bukuserver import server
from bukuserver.views import BookmarkModelView, TagModelView


@pytest.fixture()
def app(tmp_path):
    app = server.create_app((tmp_path / "test.db").as_posix())
    app.config.update(
        {
            "TESTING": True,
        }
    )
    # other setup can go here
    yield app
    # clean up / reset resources here


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()


def get_tmp_bukudb(tmp_path):
    return BukuDb(dbfile=(tmp_path / "test.db").as_posix())


@pytest.mark.parametrize('disable_favicon', [False, True])
def test_bookmark_model_view(tmp_path, disable_favicon, app):
    inst = BookmarkModelView(get_tmp_bukudb(tmp_path))
    model = Namespace(description="randomdesc", id=1, tags="tags1", title="Example Domain", url="http://example.com")
    app.config["BUKUSERVER_DISABLE_FAVICON"] = disable_favicon
    with app.test_request_context():
        assert inst._list_entry(None, model, "Entry")


@pytest.fixture
def tmv_instance(tmp_path):
    """define tag model view instance"""
    inst = TagModelView(get_tmp_bukudb(tmp_path))
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
    inst = BookmarkModelView(get_tmp_bukudb(tmp_path))
    return inst


@pytest.mark.parametrize('url, exp_url', [
    ['http://example.com', 'http://example.com'],
    ['/bookmark/', None],
])
def test_bmv_create_form(bmv_instance, url, exp_url, app):
    with app.test_request_context():
        request.args = {"url": url}
        form = bmv_instance.create_form()
        assert form.url.data == exp_url
