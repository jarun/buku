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


def test_home(tmp_path):
    test_db = tmp_path / 'test.db'
    app = server.create_app(test_db.as_posix())
    client = app.test_client()
    rd = client.get('/')
    assert rd.status_code == 200
    assert not flask.g.bukudb.get_rec_all()
