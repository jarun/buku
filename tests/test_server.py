from typing import Any, Dict
import pytest
import flask
from flask_api.status import HTTP_405_METHOD_NOT_ALLOWED
from click.testing import CliRunner
from bukuserver import server
from bukuserver.response import Response
from bukuserver.server import get_bool_from_env_var


def assert_response(response, exp_res: Response, data: Dict[str, Any] = None):
    assert response.status_code == exp_res.status_code
    assert response.get_json() == exp_res.json(data=data)


@pytest.mark.parametrize(
    'data, exp_json', [
        [None, {'status': 0, 'message': 'Success.'}],
        [{}, {'status': 0, 'message': 'Success.'}],
        [{'key': 'value'}, {'status': 0, 'message': 'Success.', 'key': 'value'}],
    ]
)
def test_response_json(data, exp_json):
    assert Response.SUCCESS.json(data=data) == exp_json


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
    'method, url, exp_res, data', [
        ['get', '/api/tags', Response.SUCCESS, {'tags': []}],
        ['get', '/api/bookmarks', Response.SUCCESS, {'bookmarks': []}],
        ['get', '/api/bookmarks/search', Response.SUCCESS, {'bookmarks': []}],
        ['post', '/api/bookmarks/refresh', Response.FAILURE, None]
    ]
)
def test_api_empty_db(client, method, url, exp_res, data):
    rd = getattr(client, method)(url)
    assert_response(rd, exp_res, data)


@pytest.mark.parametrize(
    'url, methods', [
        ['api/tags', ['post', 'put', 'delete']],
        ['/api/tags/tag1', ['post']],
        ['api/bookmarks', ['put']],
        ['/api/bookmarks/1', ['post']],
        ['/api/bookmarks/refresh', ['get', 'put', 'delete']],
        ['api/bookmarks/1/refresh', ['get', 'put', 'delete']],
        ['api/bookmarks/1/tiny', ['post', 'put', 'delete']],
        ['/api/bookmarks/1/2', ['post']],
    ]
)
def test_not_allowed(client, url, methods):
    for method in methods:
        rd = getattr(client, method)(url)
        assert rd.status_code == HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.parametrize(
    'method, url, json, exp_res', [
        ['get', '/api/tags/tag1', None, Response.TAG_NOT_FOUND],
        ['put', '/api/tags/tag1', {'tags': ['tag2']}, Response.TAG_NOT_FOUND],
        ['delete', '/api/tags/tag1', None, Response.TAG_NOT_FOUND],
        ['get', '/api/bookmarks/1', None, Response.BOOKMARK_NOT_FOUND],
        ['put', '/api/bookmarks/1', {'title': 'none'}, Response.FAILURE],
        ['delete', '/api/bookmarks/1', None, Response.FAILURE],
        ['post', '/api/bookmarks/1/refresh', None, Response.FAILURE],
        ['get', '/api/bookmarks/1/tiny', None, Response.FAILURE],
        ['get', '/api/bookmarks/1/2', None, Response.RANGE_NOT_VALID],
        ['put', '/api/bookmarks/1/2', {1: {'title': 'one'}, 2: {'title': 'two'}}, Response.RANGE_NOT_VALID],
        ['delete', '/api/bookmarks/1/2', None, Response.RANGE_NOT_VALID],
    ]
)
def test_invalid_id(client, method, url, json, exp_res):
    rd = getattr(client, method)(url, json=json)
    assert_response(rd, exp_res)


def test_tag_api(client):
    url = 'http://google.com'
    rd = client.post('/api/bookmarks', json={'url': url, 'tags': ['tag1', 'TAG2']})
    assert_response(rd, Response.SUCCESS)
    rd = client.get('/api/tags')
    assert_response(rd, Response.SUCCESS, {'tags': ['tag1', 'tag2']})
    rd = client.get('/api/tags/tag1')
    assert_response(rd, Response.SUCCESS, {'name': 'tag1', 'usage_count': 1})
    rd = client.put('/api/tags/tag1', json={'tags': 'string'})
    assert_response(rd, Response.INPUT_NOT_VALID, data={'errors': {'tags': 'List of tags expected.'}})
    for json in [{}, {'tags': None}, {'tags': ''}, {'tags':[]}]:
        rd = client.put('/api/tags/tag1', json={'tags': []})
        assert_response(rd, Response.INPUT_NOT_VALID, data={'errors': {'tags': [['This field is required.']]}})
    rd = client.put('/api/tags/tag1', json={'tags': ['ok', '', None]})
    errors = {'tags': [[], ['This field is required.'], ['This field is required.']]}
    assert_response(rd, Response.INPUT_NOT_VALID, data={'errors': errors})
    rd = client.put('/api/tags/tag1', json={'tags': ['one,two', 3,]})
    errors = {'tags': [['Tag must not contain delimiter \",\".'], ['Tag must be a string.']]}
    assert_response(rd, Response.INPUT_NOT_VALID, data={'errors': errors})
    rd = client.put('/api/tags/tag1', json={'tags': ['tag3', 'TAG 4']})
    assert_response(rd, Response.SUCCESS)
    rd = client.get('/api/tags')
    assert_response(rd, Response.SUCCESS, {'tags': ['tag 4', 'tag2', 'tag3']})
    rd = client.put('/api/tags/tag 4', json={'tags': ['tag5']})
    assert_response(rd, Response.SUCCESS)
    rd = client.get('/api/tags')
    assert_response(rd, Response.SUCCESS, {'tags': ['tag2', 'tag3', 'tag5']})
    rd = client.delete('/api/tags/tag3')
    assert_response(rd, Response.SUCCESS)
    rd = client.delete('/api/tags/tag3')
    assert_response(rd, Response.TAG_NOT_FOUND)
    rd = client.delete('/api/tags/tag,2')
    assert_response(rd, Response.TAG_NOT_VALID)
    rd = client.get('/api/bookmarks/1')
    assert_response(rd, Response.SUCCESS, {'description': '', 'tags': ['tag2', 'tag5'], 'title': 'Google', 'url': url})


def test_bookmark_api(client):
    url = 'http://google.com'
    rd = client.post('/api/bookmarks', json={})
    errors = {'url': ['This field is required.']}
    assert_response(rd, Response.INPUT_NOT_VALID, data={'errors': errors})
    rd = client.post('/api/bookmarks', json={'url': url})
    assert_response(rd, Response.SUCCESS)
    rd = client.post('/api/bookmarks', json={'url': url})
    assert_response(rd, Response.FAILURE)
    rd = client.get('/api/bookmarks')
    assert_response(rd, Response.SUCCESS, {'bookmarks': [{'description': '', 'tags': [], 'title': 'Google', 'url': url}]})
    rd = client.get('/api/bookmarks/1')
    assert_response(rd, Response.SUCCESS, {'description': '', 'tags': [], 'title': 'Google', 'url': url})
    rd = client.put('/api/bookmarks/1', json={'tags': 'not a list'})
    assert_response(rd, Response.INPUT_NOT_VALID, data={'errors': {'tags': 'List of tags expected.'}})
    rd = client.put('/api/bookmarks/1', json={'tags': ['tag1', 'tag2']})
    assert_response(rd, Response.SUCCESS)
    rd = client.put('/api/bookmarks/1', json={})
    assert_response(rd, Response.SUCCESS)
    rd = client.get('/api/bookmarks/1')
    assert_response(rd, Response.SUCCESS, {'description': '', 'tags': ['tag1', 'tag2'], 'title': 'Google', 'url': url})
    rd = client.put('/api/bookmarks/1', json={'tags': [], 'description': 'Description'})
    assert_response(rd, Response.SUCCESS)
    rd = client.get('/api/bookmarks/1')
    assert_response(rd, Response.SUCCESS, {'description': 'Description', 'tags': [], 'title': 'Google', 'url': url})


@pytest.mark.parametrize('d_url', ['/api/bookmarks', '/api/bookmarks/1'])
def test_bookmark_api_delete(client, d_url):
    url = 'http://google.com'
    rd = client.post('/api/bookmarks', json={'url': url})
    assert_response(rd, Response.SUCCESS)
    rd = client.delete(d_url)
    assert_response(rd, Response.SUCCESS)


@pytest.mark.parametrize('api_url', ['/api/bookmarks/refresh', '/api/bookmarks/1/refresh'])
def test_refresh_bookmark(client, api_url):
    url = 'http://google.com'
    rd = client.post('/api/bookmarks', json={'url': url})
    assert_response(rd, Response.SUCCESS)
    rd = client.post(api_url)
    assert_response(rd, Response.SUCCESS)
    rd = client.get('/api/bookmarks/1')
    assert_response(rd, Response.SUCCESS, {'description': '', 'tags': [], 'title': 'Google', 'url': url})


@pytest.mark.parametrize(
    'url, exp_res, data', [
        ['http://google.com', Response.SUCCESS, {'url': 'http://tny.im/2'}],
        ['chrome://bookmarks/', Response.FAILURE, None],
    ])
def test_get_tiny_url(client, url, exp_res, data):
    rd = client.post('/api/bookmarks', json={'url': url})
    assert_response(rd, Response.SUCCESS)
    rd = client.get('/api/bookmarks/1/tiny')
    assert_response(rd, exp_res, data)


@pytest.mark.parametrize('kwargs, exp_res, data', [
    [
        {"data": {'url': 'http://google.com'}},
        Response.SUCCESS,
        {'bad url': 0, 'recognized mime': 0, 'tags': None, 'title': 'Google'}
    ],
    [{}, Response.FAILURE, None],
    [
        {"data": {'url': 'chrome://bookmarks/'}},
        Response.SUCCESS,
        {'bad url': 1, 'recognized mime': 0, 'tags': None, 'title': None}
    ],
])
def test_network_handle(client, kwargs, exp_res, data):
    rd = client.post('/api/network_handle', **kwargs)
    assert rd.status_code == exp_res.status_code
    rd_json = rd.get_json()
    rd_json.pop('description', None)
    assert rd_json == exp_res.json(data=data)


def test_bookmark_range_api(client):
    kwargs_list = [
        {"json": {'url': 'http://google.com'}},
        {"json": {'url': 'http://example.com'}}]
    for kwargs in kwargs_list:
        rd = client.post('/api/bookmarks', **kwargs)
        assert_response(rd, Response.SUCCESS)

    rd = client.put('/api/bookmarks/1/2', json={
        '1': {'tags': ['tag1 A', 'tag1 B', 'tag1 C']},
        '2': {'tags': ['tag2']}
    })
    assert_response(rd, Response.SUCCESS)
    rd = client.get('/api/bookmarks/1/2')
    assert_response(rd, Response.SUCCESS, {'bookmarks': {
        '1': {'description': '', 'tags': ['tag1 a', 'tag1 b', 'tag1 c'], 'title': 'Google', 'url': 'http://google.com'},
        '2': {'description': '', 'tags': ['tag2',], 'title': 'Example Domain', 'url': 'http://example.com'}}})
    rd = client.put('/api/bookmarks/1/2', json={
        '1': {'title': 'Bookmark 1', 'tags': ['tag1 C', 'tag1 A'], 'del_tags': True},
        '2': {'title': 'Bookmark 2', 'tags': ['-', 'tag2'], 'del_tags': False}
    })
    assert_response(rd, Response.SUCCESS)
    rd = client.get('/api/bookmarks/1/2')
    assert_response(rd, Response.SUCCESS, {'bookmarks': {
        '1': {'description': '', 'tags': ['tag1 b'], 'title': 'Bookmark 1', 'url': 'http://google.com'},
        '2': {'description': '', 'tags': ['-', 'tag2',], 'title': 'Bookmark 2', 'url': 'http://example.com'}}})

    rd = client.put('/api/bookmarks/2/1', json={})
    assert_response(rd, Response.RANGE_NOT_VALID)

    rd = client.put('/api/bookmarks/1/2', json={})
    assert_response(rd, Response.INPUT_NOT_VALID, data={
        'errors': {
            '1': 'Input required.',
            '2': 'Input required.'
        }
    })
    rd = client.put('/api/bookmarks/1/2', json={'1': {'tags': []}})
    assert_response(rd, Response.INPUT_NOT_VALID, data={'errors': {'2': 'Input required.'}})
    rd = client.put('/api/bookmarks/1/2', json={
        '1': {'tags': ['ok', 'with,delim']},
        '2': {'tags': 'string'},
    })
    assert_response(rd, Response.INPUT_NOT_VALID, data={
        'errors': {
            '1': {'tags': [[], ['Tag must not contain delimiter \",\".']]},
            '2': {'tags': 'List of tags expected.'}
        }
    })
    rd = client.get('/api/bookmarks/2/1')
    assert_response(rd, Response.RANGE_NOT_VALID)
    rd = client.delete('/api/bookmarks/1/2')
    assert_response(rd, Response.SUCCESS)
    rd = client.get('/api/bookmarks')
    assert_response(rd, Response.SUCCESS, {'bookmarks': []})


def test_bookmark_search(client):
    rd = client.post('/api/bookmarks', json={'url': 'http://google.com'})
    assert_response(rd, Response.SUCCESS)
    rd = client.get('/api/bookmarks/search', query_string={'keywords': ['google']})
    assert_response(rd, Response.SUCCESS, {'bookmarks': [
        {'description': '', 'id': 1, 'tags': [], 'title': 'Google', 'url': 'http://google.com'}]})
    rd = client.delete('/api/bookmarks/search', data={'keywords': ['google']})
    assert_response(rd, Response.SUCCESS)
    rd = client.get('/api/bookmarks')
    assert_response(rd, Response.SUCCESS, {'bookmarks': []})


@pytest.mark.parametrize('env_val, exp_val', [
    ['true', True],
    ['false', False],
    ['0', False],
    ['1', True],
    [None, True],
    ['random', True]
])
def test_get_bool_from_env_var(monkeypatch, env_val, exp_val):
    key = 'BUKUSERVER_TEST'
    if env_val is not None:
        monkeypatch.setenv(key, env_val)
    assert get_bool_from_env_var(key, True) == exp_val
