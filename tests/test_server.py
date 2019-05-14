from click.testing import CliRunner
import flask
import pytest

from bukuserver import server

@pytest.mark.parametrize(
    'args,word',
    [
        ('--help', 'bukuserver'),
        ('--version', 'Buku')
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
        ['/api/bookmarks/search', {'bookmarks': []}]
    ]
)
def test_api_empty_db(client, url, exp_res):
    rd = client.get(url)
    assert rd.status_code == 200
    assert rd.get_json() == exp_res


@pytest.mark.parametrize(
    'url, exp_res, status_code, method', [
        ['/api/tags/1', {'message': 'This resource does not exist.'}, 404, 'get'],
        ['/api/tags/1', {'message': 'failure', 'status': 1}, 400, 'put'],
        ['/api/bookmarks/1', {'message': 'failure', 'status': 1}, 400, 'get'],
        ['/api/bookmarks/1', None, 400, 'put'],
        ['/api/bookmarks/1', {'message': 'failure', 'status': 1}, 400, 'delete'],
    ]
)
def test_invalid_id(client, url, exp_res, status_code, method):
    rd = getattr(client, method)(url)
    assert rd.status_code == status_code
    assert rd.get_json() == exp_res


def test_bookmark_api(client):
    url = 'http://google.com'
    rd = client.post('/api/bookmarks', data={'url': url})
    assert rd.status_code == 200
    assert rd.get_json() == {'message': 'success', 'status': 0}
    rd = client.post('/api/bookmarks', data={'url': url})
    assert rd.status_code == 400
    assert rd.get_json() == {'message': 'failure', 'status': 1}
    rd = client.get('/api/bookmarks/search', query_string={'keywords': 'google.com'})
    assert rd.status_code == 200
    assert rd.get_json() == {'bookmarks': [
        {'description': '', 'id': 1, 'tags': [], 'title': '', 'url': url}]}
    rd = client.get('/api/bookmarks/1')
    assert rd.status_code == 200
    assert rd.get_json() == {
        'description': '', 'tags': [], 'title': '', 'url': 'http://google.com'}
