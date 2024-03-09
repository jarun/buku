"""test for views.

resources: https://flask.palletsprojects.com/en/2.2.x/testing/
"""
from argparse import Namespace

import pytest
from flask import request
from lxml import etree

from buku import BukuDb
from bukuserver import server
from bukuserver.views import BookmarkModelView, TagModelView
from tests.util import mock_fetch, _add_rec


@pytest.fixture()
def dbfile(tmp_path):
    return (tmp_path / "test.db").as_posix()

@pytest.fixture()
def app(dbfile):
    app = server.create_app(dbfile)
    app.config.update({'TESTING': True, 'WTF_CSRF_ENABLED': False})
    # other setup can go here
    yield app
    # clean up / reset resources here

def env_fixture(name, **kwargs):
    """Produces a fixture that mocks a test parameter directly in an env var (before app init)"""
    def _env_fixture(dbfile, monkeypatch, request):
        if request.param is not None:  # default value placeholder
            monkeypatch.setenv(name, str(request.param))
        app = server.create_app(dbfile)
        app.config.update({'TESTING': True, 'WTF_CSRF_ENABLED': False})
        return request.param
    return pytest.fixture(**kwargs)(_env_fixture)


@pytest.fixture()
def client(app):
    return app.test_client()

@pytest.fixture()
def runner(app):
    return app.test_cli_runner()

@pytest.fixture()
def bukudb(dbfile):
    return BukuDb(dbfile=dbfile)

@pytest.fixture
def tmv_instance(bukudb):
    """define tag model view instance"""
    return TagModelView(bukudb)

@pytest.fixture
def bmv_instance(bukudb):
    """define tag model view instance"""
    return BookmarkModelView(bukudb)


@pytest.mark.parametrize('disable_favicon', [False, True])
def test_bookmark_model_view(bukudb, disable_favicon, app):
    inst = BookmarkModelView(bukudb)
    model = Namespace(description="randomdesc", id=1, tags="tags1", title="Example Domain", url="http://example.com")
    app.config["BUKUSERVER_DISABLE_FAVICON"] = disable_favicon
    with app.test_request_context():
        assert inst._list_entry(None, model, "Entry")


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
    _add_rec(tmv_instance.bukudb, 'http://example.com/1.jpg', tags_in='t1,t2,t3')
    _add_rec(tmv_instance.bukudb, 'http://example.com/2.jpg', tags_in='t2,t3')
    _add_rec(tmv_instance.bukudb, 'http://example.com/3.jpg', tags_in='t3')
    res = tmv_instance.get_list(0, sort_field, sort_desc, None, filters)
    assert res == exp_res


@pytest.mark.parametrize('url, backlink', [
    ['http://example.com', None],
    ['http://example.com', '/bookmark/'],
])
def test_bmv_create_form(bmv_instance, url, backlink, app):
    with app.test_request_context():
        request.args = {'link': url, 'url': backlink} if backlink else {'link': url}
        form = bmv_instance.create_form()
        assert form.url.data == url


#
# -= functional tests =-
#

xpath_alert = lambda kind, message: f'//div[@class="alert alert-{kind} alert-dismissable"][contains(., "{message}")]'

def assert_success_alert(dom, edit, id=1):
    message = f'Record was successfully {"saved" if edit else "created"}.'
    assert dom.xpath(xpath_alert('success', message)), 'alert missing'
    assert dom.xpath(f'//script[contains(., "const SUCCESS = [")][contains(., "{message}")][contains(., "/bookmark/details/?id={id}&")]')

def assert_failure_alert(dom, edit):
    assert dom.xpath(xpath_alert('danger', f'Failed to {"update" if edit else "create"} record. Duplicate URL')), 'alert missing'
    assert not dom.xpath('//script[contains(., "const SUCCESS = [")][contains(., "/bookmark/details/?id=")]')

def assert_response(response, uri, *, status=200, argnames=None, args=None):
    assert response.status_code == status
    assert response.request.path == uri
    if argnames is not None:
        assert set(response.request.args) == set(argnames)
    if args is not None:
        assert dict(response.request.args) == args
    return etree.HTML(response.text)

def assert_bookmark(bookmark, query, tags=None):
    assert bookmark.url == query['link']
    assert bookmark.title == query['title']
    assert bookmark.desc == query['description']
    assert bookmark.tags == tags or query['tags']


@pytest.mark.gui
@pytest.mark.slow
@pytest.mark.parametrize('exists, uri, tab, args', [
    (False, '/bookmark/new/', 'Create', ['link', 'title', 'description']),
    (True, '/bookmark/edit/', 'Edit', ['id']),
])
def test_bookmarklet_view(bukudb, client, exists, uri, tab, args):
    query = {'url': 'http://example.com', 'title': 'Sample site', 'description': 'Foo bar baz'}
    if exists:
        _add_rec(bukudb, query['url'])

    response = client.get('/bookmarklet', query_string=query, follow_redirects=True)
    dom = assert_response(response, uri, argnames=args)
    assert dom.xpath('//ul[@class="nav nav-tabs"]/li[@class="active"]/a/text()') == [tab]
    assert dom.xpath('//input[@name="link"]/@value') == [query['url']]
    assert bool(dom.xpath('//input[@name="id"]')) == exists


@pytest.mark.gui
@pytest.mark.slow
@pytest.mark.parametrize('fetch, title, desc', [
    (True, 'Some title', ''),
    (True, '', 'Some description'),
    (False, 'Some title', ''),
    (False, '', 'Some description'),
])
def test_create_and_fetch(bukudb, monkeypatch, client, fetch, title, desc):
    query = {'link': 'http://example.com', 'title': title, 'description': desc, 'tags': 'foo, bar, baz'}
    _title, _desc = 'Sample site', 'Foo bar baz'
    if fetch:
        query['fetch'] = 'on'

    with mock_fetch(title=_title, desc=_desc):
        response = client.post('/bookmark/new/', data=query, follow_redirects=True)
    dom = assert_response(response, '/bookmark/')
    assert_success_alert(dom, edit=False)
    [bookmark] = bukudb.get_rec_all()
    assert_bookmark(bookmark, {
        'link': query['link'], 'tags': ',bar,baz,foo,',
        'title': (title or _title) if fetch else title,
        'description': (desc or _desc) if fetch else desc,
    })


@pytest.mark.gui
@pytest.mark.slow
@pytest.mark.parametrize('redirect, uri, args', [
    ('_add_another', '/bookmark/new/', {}),
    ('_continue_editing', '/bookmark/edit/', {'id': '1', 'url': '/bookmark/'}),
])
def test_create_redirect(client, redirect, uri, args):
    query = {'link': 'http://example.com', 'title': '', 'description': '', 'tags': '', redirect: 'on'}

    response = client.post('/bookmark/new/', data=query, follow_redirects=True)
    dom = assert_response(response, uri, args=args)
    assert_success_alert(dom, edit=False)


@pytest.mark.gui
@pytest.mark.slow
def test_create_duplicate(bukudb, client):
    query = {'link': 'http://example.com', 'title': '', 'description': '', 'tags': ''}
    _add_rec(bukudb, query['link'])

    response = client.post('/bookmark/new/', data=query, follow_redirects=True)
    dom = assert_response(response, '/bookmark/new/')
    assert_failure_alert(dom, edit=False)


@pytest.mark.gui
@pytest.mark.slow
@pytest.mark.parametrize('override', [False, True])
def test_update(bukudb, client, override):
    _add_rec(bukudb, 'http://example.org')
    query = {'link': 'http://example.com', 'title': 'Sample site', 'description': 'Foo bar baz', 'tags': 'foo, bar, baz'}
    if override:
        _add_rec(bukudb, query['link'])

    response = client.post('/bookmark/edit/', query_string={'id': 1}, data=query, follow_redirects=True)
    if override:
        dom = assert_response(response, '/bookmark/edit/')
        assert_failure_alert(dom, edit=True)
    else:
        dom = assert_response(response, '/bookmark/')
        assert_success_alert(dom, edit=True)
        [bookmark] = bukudb.get_rec_all()
        assert_bookmark(bookmark, query, tags=',bar,baz,foo,')


@pytest.mark.gui
@pytest.mark.slow
@pytest.mark.parametrize('redirect, uri, args', [
    ('_add_another', '/bookmark/new/', {'url': '/bookmark/'}),
    ('_continue_editing', '/bookmark/edit/', {'id': '1'}),
])
def test_update_redirect(bukudb, client, redirect, uri, args):
    _add_rec(bukudb, 'http://example.org')
    query = {'link': 'http://example.com', 'title': 'Sample site', 'description': 'Foo bar baz', 'tags': 'foo, bar, baz', redirect: 'on'}

    response = client.post('/bookmark/edit/', query_string={'id': 1}, data=query, follow_redirects=True)
    dom = assert_response(response, uri, args=args)
    assert_success_alert(dom, edit=True)
    [bookmark] = bukudb.get_rec_all()
    assert_bookmark(bookmark, query, tags=',bar,baz,foo,')


@pytest.mark.gui
@pytest.mark.slow
@pytest.mark.parametrize('exists', [True, False])
def test_delete(client, bukudb, exists):
    if exists:
        _add_rec(bukudb, 'http://example.com')

    response = client.post('/bookmark/delete/', data={'id': 1}, follow_redirects=True)
    dom = assert_response(response, '/bookmark/')
    assert dom.xpath(xpath_alert('success', 'Record was successfully deleted.') if exists else
                     xpath_alert('danger', 'Record does not exist.'))


@pytest.mark.gui
@pytest.mark.slow
@pytest.mark.parametrize('total, per_page, pages, last_page', [
    (0, 5, 1, 0),
    (1, 5, 1, 1),
    (5, 5, 1, 5),
    (6, 5, 2, 1),
    (9, 5, 2, 4),
    (10, 5, 2, 5),
    (11, 5, 3, 1),
    (9, None, 1, 9),
    (10, None, 1, 10),
    (11, None, 2, 1),
    (14, 15, 1, 14),
    (15, 15, 1, 15),
    (16, 15, 2, 1),
])
def test_env_per_page(bukudb, app, client, total, per_page, pages, last_page):
    for i in range(1, total+1):
        _add_rec(bukudb, f'http://example.com/{i}')
    if per_page:
        app.config.update({'BUKUSERVER_PER_PAGE': per_page})

    response = client.get('/bookmark/last-page', follow_redirects=True)
    dom = assert_response(response, '/bookmark/', args={'page': str(pages - 1)})
    cells = dom.xpath('//td[@class="col-Entry"]')
    assert len(cells) == last_page
    for i, cell in enumerate(cells, start=1):
        url = f'http://example.com/{total - last_page + i}'
        assert cell.xpath(f'//a[@href="{url}"]/text()') == ['<EMPTY TITLE>', url]


@pytest.mark.gui
@pytest.mark.slow
@pytest.mark.parametrize('new_tab', [False, True, None])
@pytest.mark.parametrize('favicons', [False, True, None])
@pytest.mark.parametrize('mode', ['full', 'netloc', None])
def test_env_entry_render_params(bukudb, app, client, mode, favicons, new_tab):
    url, netloc, title, desc, tags = 'http://example.com', 'example.com', 'Sample site', 'Foo bar baz', ',bar,baz,foo,'
    _add_rec(bukudb, url, title, tags, desc)
    _tags = tags.strip(',').split(',')
    if mode:
        app.config.update({'BUKUSERVER_URL_RENDER_MODE': mode})
    if favicons is not None:
        app.config.update({'BUKUSERVER_DISABLE_FAVICON': not favicons})
    if new_tab is not None:
        app.config.update({'BUKUSERVER_OPEN_IN_NEW_TAB': new_tab})

    dom = assert_response(client.get('/bookmark/'), '/bookmark/')
    cell = ' '.join(etree.tostring(dom.xpath('//td[@class="col-Entry"]')[0], encoding='unicode').strip().split())
    target = '' if not new_tab else ' target="_blank"'
    icon = '' if not favicons else f'<img src="http://www.google.com/s2/favicons?domain={netloc}"/> '
    prefix = f'<td class="col-Entry"> {icon}<a href="{url}"{target}>{title}</a>'
    suffix = (''.join(f'<a class="btn btn-default" href="/bookmark/?flt0_tags_contain={s}">{s}</a>' for s in _tags) +
              f'<br/>{desc} </td>')
    if mode == 'netloc':
        assert cell == prefix + f' (<a href="/bookmark/?flt0_url_netloc_match={netloc}">{netloc}</a>)<br/>' + suffix
    else:
        assert cell == (prefix + f'<br/><a href="{url}"{target}>{url}</a><br/>' +
                        f'<a class="btn btn-default" href="/bookmark/?flt0_url_netloc_match={netloc}">netloc:{netloc}</a>' +
                        suffix)


readonly = env_fixture('BUKUSERVER_READONLY', params=[False, True, None])

@pytest.mark.gui
@pytest.mark.slow
def test_env_readonly(bukudb, readonly, client):
    _add_rec(bukudb, 'http://example.com')
    edit = not readonly

    response = client.get('/bookmark/')
    dom = assert_response(response, '/bookmark/')
    assert bool(dom.xpath('//td[@class="list-buttons-column"]/a[@title="Edit Record"]')) == edit, 'edit icon'
    assert bool(dom.xpath('//td[@class="list-buttons-column"]/form[@action="/bookmark/delete/"]')) == edit, 'delete icon'

    response = client.get('/bookmark/details/', query_string={'id': 1})
    dom = assert_response(response, '/bookmark/details/')
    assert (dom.xpath('//ul[@class="nav nav-tabs"]/li/a/text()') ==
            (['List', 'Details'] if readonly else ['List', 'Create', 'Edit', 'Details']))

    response = client.get('/bookmark/new/', follow_redirects=True)
    assert_response(response, '/bookmark/' if readonly else '/bookmark/new/')
    response = client.get('/bookmark/edit/', query_string={'id': 1}, follow_redirects=True)
    assert_response(response, '/bookmark/' if readonly else '/bookmark/edit/')


proxy_path = env_fixture('BUKUSERVER_REVERSE_PROXY_PATH', params=['', '/buku', None])

@pytest.mark.gui
@pytest.mark.slow
def test_env_reverse_proxy_path(proxy_path, client):
    links = [(proxy_path or '') + s for s in ['/', '/bookmark/', '/tag/', '/statistic/']]

    dom = assert_response(client.get(links[0]), links[0])
    assert dom.xpath('//nav[@class="navbar navbar-default"]//a/@href') == ['/'] + links
    body_links = dom.xpath('//main//a/@href')
    assert body_links[-1].startswith('javascript:')
    assert body_links[:-1] == links[1:]
    assert dom.xpath('//main//form/@action') == [links[0]]

    for link in links[1:]:
        assert_response(client.get(link), link)


theme = env_fixture('BUKUSERVER_THEME', params=['default', 'slate', None])

@pytest.mark.gui
@pytest.mark.slow
def test_env_theme(theme, client):
    dom = assert_response(client.get('/'), '/')
    assert dom.xpath('//head/link[@rel="stylesheet"][@href=$href]',
                     href=f'/static/admin/bootstrap/bootstrap3/swatch/{theme or "default"}/bootstrap.min.css?v=3.3.5')


_DICT = {
    'en': {'//ul[@class="nav navbar-nav"]/li/a/text()': ['Home', 'Bookmarks', 'Tags', 'Statistic'],
           '//ul[@class="nav nav-tabs actions-nav"]/li/a/text()': ['List (1)', 'Create', 'Add Filter', '10 items'],
           '//td[@class="list-buttons-column"]/a/@title': ['View Record', 'Edit Record'],
           '//td[@class="list-buttons-column"]/form/button/@title': ['Delete record']},
    'de': {'//ul[@class="nav navbar-nav"]/li/a/text()': ['Start', 'Bookmarks', 'Tags', 'Statistic'],
           '//ul[@class="nav nav-tabs actions-nav"]/li/a/text()': ['Liste (1)', 'Erstellen', 'Filter hinzufügen', '10 Elemente'],
           '//td[@class="list-buttons-column"]/a/@title': ['Eintrag ansehen', 'Eintrag bearbeiten'],
           '//td[@class="list-buttons-column"]/form/button/@title': ['Delete record']},
    'fr': {'//ul[@class="nav navbar-nav"]/li/a/text()': ['Accueil', 'Bookmarks', 'Tags', 'Statistic'],
           '//ul[@class="nav nav-tabs actions-nav"]/li/a/text()': ['Liste (1)', 'Créer', 'Ajouter un filtre', '10 items'],
           '//td[@class="list-buttons-column"]/a/@title': ['Afficher L\'enregistrement', 'Modifier enregistrement'],
           '//td[@class="list-buttons-column"]/form/button/@title': ['Delete record']},
    'ru': {'//ul[@class="nav navbar-nav"]/li/a/text()': ['Главная', 'Bookmarks', 'Tags', 'Statistic'],
           '//ul[@class="nav nav-tabs actions-nav"]/li/a/text()': ['Список (1)', 'Создать', 'Добавить Фильтр', '10 элементы'],
           '//td[@class="list-buttons-column"]/a/@title': ['Просмотр записи', 'Редактировать запись'],
           '//td[@class="list-buttons-column"]/form/button/@title': ['Delete record']},
}

@pytest.mark.gui
@pytest.mark.slow
@pytest.mark.parametrize('locale', ['en', 'de', 'fr', 'ru', None])
def test_env_locale(bukudb, app, client, locale):
    strings = _DICT[locale or 'en']
    _add_rec(bukudb, 'http://example.com')
    if locale:
        app.config.update({'BUKUSERVER_LOCALE': locale})

    dom = assert_response(client.get('/bookmark/'), '/bookmark/')
    for k, v in strings.items():
        assert [s.strip() for s in dom.xpath(k) if s.strip()] == v
