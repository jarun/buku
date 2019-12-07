from argparse import Namespace

import pytest
from flask import current_app

from buku import BukuDb
from bukuserver import server
from bukuserver.views import BookmarkModelView


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
    test_db = tmp_path / 'test.db'
    bukudb = BukuDb(dbfile=test_db.as_posix())
    inst = BookmarkModelView(bukudb)
    model = Namespace(
        description='randomdesc', id=1, tags='tags1',
        title='Example Domain', url='http://example.com')
    #  __import__('pdb').set_trace()
    current_app.config['BUKUSERVER_DISABLE_FAVICON'] = disable_favicon
    img_html = ''
    if not disable_favicon:
        img_html = \
            '<img src="http://www.google.com/s2/favicons?domain=example.com"/> '
    res = inst._list_entry(None, model, 'Entry')
    exp_res = \
        (
            '<a href="http://example.com">Example Domain</a><br/>'
            '<a href="http://example.com">http://example.com</a><br/>'
            '<a class="btn btn-default" '
            'href="/bookmark/?flt2_url_netloc_match=example.com">netloc:example.com</a>'
            '<a class="btn btn-default" href="/bookmark/?flt2_tags_contain=tags1">tags1</a>'
            '<br/>randomdesc')
    exp_res = ''.join([img_html, exp_res])
    assert str(res) == exp_res
