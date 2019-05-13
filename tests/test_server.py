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
