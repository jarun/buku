import json

import pytest
import flask
from click.testing import CliRunner

from bukuserver import server
from bukuserver.response import response_template

@pytest.mark.parametrize(
    'args,word',
    [
        ('--help', 'bukuserver'),
        ('--version', 'buku')
    ]
)
def test_cli(args, word):
    runner = CliRunner()
    result = runner.invoke(server.cli, [args])
    assert result.exit_code == 0
    assert word in result.output


@pytest.fixture
def client(tmp_path):
    test_db = tmp_path / 'test.db'
    app = server.create_app(test_db.as_posix())
    client = app.test_client()
    return client


def test_home(client):
    rd = client.get('/')
    assert rd.status_code == 200
    assert not flask.g.bukudb.get_rec_all()


@pytest.mark.parametrize(
    'url, exp_res', [
        ['/api/tags', {'tags': []}],
        ['/api/bookmarks', {'bookmarks': []}],
        ['/api/bookmarks/search', {'bookmarks': []}],
        ['/api/bookmarks/refresh', response_template['failure']]
    ]
)
def test_api_empty_db(client, url, exp_res):
    if url == '/api/bookmarks/refresh':
        rd = client.post(url)
        assert rd.status_code == 400
    else:
        rd = client.get(url)
        assert rd.status_code == 200
    assert rd.get_json() == exp_res


@pytest.mark.parametrize(
    'url, exp_res, status_code, method', [
        ['/api/tags/1', {'message': 'This resource does not exist.'}, 404, 'get'],
        ['/api/tags/1', response_template['failure'], 400, 'put'],
        ['/api/bookmarks/1', response_template['failure'], 400, 'get'],
        ['/api/bookmarks/1', response_template['failure'], 400, 'put'],
        ['/api/bookmarks/1', response_template['failure'], 400, 'delete'],
        ['/api/bookmarks/1/refresh', response_template['failure'], 400, 'post'],
        ['/api/bookmarks/1/tiny', response_template['failure'], 400, 'get'],
        ['/api/bookmarks/1/2', response_template['failure'], 400, 'get'],
        ['/api/bookmarks/1/2', response_template['failure'], 400, 'put'],
        ['/api/bookmarks/1/2', response_template['failure'], 400, 'delete'],
    ]
)
def test_invalid_id(client, url, exp_res, status_code, method):
    rd = getattr(client, method)(url)
    assert rd.status_code == status_code
    assert rd.get_json() == exp_res


def test_tag_api(client):
    url = 'http://google.com'
    rd = client.post('/api/bookmarks', data={'url': url, 'tags': 'tag1,tag2'})
    assert rd.status_code == 200
    assert rd.get_json() == response_template['success']
    rd = client.get('/api/tags')
    assert rd.status_code == 200
    assert rd.get_json() == {'tags': ['tag1', 'tag2']}
    rd = client.get('/api/tags/tag1')
    assert rd.status_code == 200
    assert rd.get_json() == {'name': 'tag1', 'usage_count': 1}
    rd = client.put('/api/tags/tag1', data={'tags': 'tag3,tag4'})
    assert rd.status_code == 200
    assert rd.get_json() == response_template['success']
    rd = client.get('/api/tags')
    assert rd.status_code == 200
    assert rd.get_json() == {'tags': ['tag2', 'tag3 tag4']}
    rd = client.put('/api/tags/tag2', data={'tags': 'tag5'})
    assert rd.status_code == 200
    assert rd.get_json() == response_template['success']
    rd = client.get('/api/tags')
    assert rd.status_code == 200
    assert rd.get_json() == {'tags': ['tag3 tag4', 'tag5']}
    rd = client.get('/api/bookmarks/1')
    assert rd.status_code == 200
    assert rd.get_json() == {
        'description': '', 'tags': ['tag3 tag4', 'tag5'], 'title': '',
        'url': 'http://google.com'}


def test_bookmark_api(client):
    url = 'http://google.com'
    rd = client.post('/api/bookmarks', data={'url': url})
    assert rd.status_code == 200
    assert rd.get_json() == response_template['success']
    rd = client.post('/api/bookmarks', data={'url': url})
    assert rd.status_code == 400
    assert rd.get_json() == response_template['failure']
    rd = client.get('/api/bookmarks')
    assert rd.status_code == 200
    assert rd.get_json() == {'bookmarks': [{
        'description': '', 'tags': [], 'title': '', 'url': 'http://google.com'}]}
    rd = client.get('/api/bookmarks/1')
    assert rd.status_code == 200
    assert rd.get_json() == {
        'description': '', 'tags': [], 'title': '', 'url': 'http://google.com'}
    rd = client.put('/api/bookmarks/1', data={'tags': [',tag1,tag2,']})
    assert rd.status_code == 200
    assert rd.get_json() == response_template['success']
    rd = client.get('/api/bookmarks/1')
    assert rd.status_code == 200
    assert rd.get_json() == {
        'description': '', 'tags': ['tag1', 'tag2'], 'title': '', 'url': 'http://google.com'}


@pytest.mark.parametrize('d_url', ['/api/bookmarks', '/api/bookmarks/1'])
def test_bookmark_api_delete(client, d_url):
    url = 'http://google.com'
    rd = client.post('/api/bookmarks', data={'url': url})
    assert rd.status_code == 200
    assert rd.get_json() == response_template['success']
    rd = client.delete(d_url)
    assert rd.status_code == 200
    assert rd.get_json() == response_template['success']


@pytest.mark.parametrize('api_url', ['/api/bookmarks/refresh', '/api/bookmarks/1/refresh'])
def test_refresh_bookmark(client, api_url):
    url = 'http://google.com'
    rd = client.post('/api/bookmarks', data={'url': url})
    assert rd.status_code == 200
    assert rd.get_json() == response_template['success']
    rd = client.post(api_url)
    assert rd.status_code == 200
    assert rd.get_json() == response_template['success']
    rd = client.get('/api/bookmarks/1')
    assert rd.status_code == 200
    json_data = rd.get_json()
    json_data.pop('description')
    assert json_data == {'tags': [], 'title': 'Google', 'url': 'http://google.com'}


@pytest.mark.parametrize(
    'url, exp_res, status_code', [
        ['http://google.com', {'url': 'http://tny.im/2'}, 200],
        ['chrome://bookmarks/', response_template['failure'], 400],
    ])
def test_get_tiny_url(client, url, exp_res, status_code):
    rd = client.post('/api/bookmarks', data={'url': url})
    assert rd.status_code == 200
    assert rd.get_json() == response_template['success']
    rd = client.get('/api/bookmarks/1/tiny')
    assert rd.status_code == status_code
    assert rd.get_json() == exp_res


@pytest.mark.parametrize('kwargs, status_code, exp_res', [
    [
        dict(data={'url': 'http://google.com'}),
        200,
        {
            'bad url': 0, 'recognized mime': 0,
            'tags': None, 'title': 'Google'}
    ],
    [{}, 400, response_template['failure']],
    [
        dict(data={'url': 'chrome://bookmarks/'}),
        200,
        {
            'bad url': 1, 'recognized mime': 0,
            'tags': None, 'title': None}
    ],
])
def test_network_handle(client, kwargs, status_code, exp_res):
    rd = client.post('/api/network_handle', **kwargs)
    assert rd.status_code == status_code
    rd_json = rd.get_json()
    rd_json.pop('description', None)
    assert rd_json == exp_res


def test_bookmark_range_api(client):
    status_code = 200
    kwargs_list = [
        dict(data={'url': 'http://google.com'}),
        dict(data={'url': 'http://example.com'})]
    for kwargs in kwargs_list:
        rd = client.post('/api/bookmarks', **kwargs)
        assert rd.status_code == status_code
    rd = client.get('/api/bookmarks/1/2')
    assert rd.status_code == status_code
    assert rd.get_json() == {
        'bookmarks': {
            '1': {'description': '', 'tags': [], 'title': '', 'url': 'http://google.com'},
            '2': {'description': '', 'tags': [], 'title': '', 'url': 'http://example.com'}}}
    put_data = json.dumps({1: {'tags': 'tag1'}, 2: {'tags': 'tag2'}})
    headers = {'content-type': 'application/json'}
    rd = client.put('/api/bookmarks/1/2', data=put_data, headers=headers)
    assert rd.status_code == status_code
    assert rd.get_json() == response_template['success']
    rd = client.delete('/api/bookmarks/1/2')
    assert rd.status_code == status_code
    assert rd.get_json() == response_template['success']
    rd = client.get('/api/bookmarks')
    assert rd.get_json() == {'bookmarks': []}


def test_bookmark_search(client):
    status_code = 200
    rd = client.post('/api/bookmarks', data={'url': 'http://google.com'})
    assert rd.status_code == status_code
    assert rd.get_json() == response_template['success']
    rd = client.get('/api/bookmarks/search', query_string={'keywords': ['google']})
    assert rd.status_code == status_code
    assert rd.get_json() == {'bookmarks': [
        {'description': '', 'id': 1, 'tags': [], 'title': '', 'url': 'http://google.com'}]}
    rd = client.delete('/api/bookmarks/search', data={'keywords': ['google']})
    assert rd.status_code == status_code
    assert rd.get_json() == response_template['success']
    rd = client.get('/api/bookmarks')
    assert rd.get_json() == {'bookmarks': []}
