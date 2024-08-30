from unittest import mock
from io import StringIO
import pytest

import buku


@pytest.fixture
def stdin(monkeypatch):
    with monkeypatch.context():
        monkeypatch.setattr('sys.stdin', (buffer := StringIO()))
        yield buffer

@pytest.fixture
def BukuDb():
    with mock.patch('buku.BukuDb') as cls:
        cls.return_value.close_quit.side_effect = SystemExit
        yield cls

@pytest.fixture
def bdb(BukuDb):
    yield BukuDb.return_value

@pytest.fixture
def piped_input():
    with mock.patch('buku.piped_input') as fn:
        yield fn

@pytest.fixture
def prompt():
    with mock.patch('buku.prompt') as fn:
        yield fn

@pytest.fixture
def exit():
    with mock.patch('sys.exit', side_effect=SystemExit) as fn:
        yield fn


def test_version(BukuDb, piped_input, capsys):
    with pytest.raises(SystemExit):
        buku.main(['--version'])
    assert capsys.readouterr().out.splitlines() == [buku.__version__]

def test_usage(BukuDb, piped_input, monkeypatch, capsys):
    with pytest.raises(SystemExit):
        buku.main(['--unknown'], program_name='buku')
    BukuDb.assert_not_called()
    assert capsys.readouterr().err.splitlines() == [
        'usage: buku [OPTIONS] [KEYWORD [KEYWORD ...]]',
        'buku: error: unrecognized arguments: --unknown',
    ]

@pytest.mark.parametrize('argv', [['--help'], ['foo', 'bar', '--help']])
def test_help(BukuDb, exit, piped_input, argv):
    with mock.patch('buku.ExtendedArgumentParser.print_help') as print_help:
        with pytest.raises(SystemExit):
            buku.main(argv)
    BukuDb.assert_not_called()
    print_help.assert_called_with()
    exit.assert_called_with(0)

@pytest.mark.parametrize('argv', [[], ['--nostdin']])
def test_prompt(BukuDb, bdb, piped_input, prompt, argv):
    with pytest.raises(SystemExit):
        buku.main(argv)
    piped_input.assert_not_called()
    BukuDb.assert_called_with()
    prompt.assert_called_with(bdb, None)
    bdb.close_quit.assert_called_with(0)


@pytest.mark.parametrize('fetch_params', [
    {'offline': True},
    {'url_redirect': True},
    {'tag_redirect': True, 'tag_error': True},
    {'url_redirect': True, 'tag_redirect': 'redirect', 'tag_error': 'error'},
    {'url_redirect': True, 'tag_redirect': 'redirect', 'del_range': [], 'del_error': range(400, 600)},
    {'url_redirect': True, 'tag_redirect': 'redirect', 'tag_error': 'error',
     'del_range': ['400-404', '500'], 'del_error': {400, 401, 402, 403, 404, 500}},
])
@pytest.mark.parametrize('value_params', [
    {'add_tags': ['foo,bar', 'baz'], 'tags_fetch': False, 'tags_in': ',bar baz,foo,', 'title': ''},
    {'tag': ['foo', 'bar,baz'], 'tags_fetch': False, 'tags_in': ',baz,foo bar,', 'title': 'Custom Title'},
    {'add_tags': ['+', 'foo', 'bar', 'baz'], 'tags_in': ',foo bar baz,', 'comment': ''},
    {'tag': ['+', 'foo,bar,baz'], 'tags_in': ',bar,baz,foo,', 'comment': 'Custom Description'},
    {'add_tags': ['-', 'foo', 'baz', 'baz'], 'tags_except': ',foo baz baz,', 'immutable': False},
    {'tag': ['-', 'foo,', ',baz,', ',baz'], 'tags_except': ',baz,foo,', 'immutable': True},
    {'add_tags': ['foo,baz,bar'], 'tag': ['baz,qux'],
     'tags_fetch': False, 'tags_in': ',bar,baz,foo,qux,'},
    {'add_tags': ['+', 'foo,baz,bar'], 'tag': ['baz,', 'qux,'],
     'tags_fetch': False, 'tags_in': ',bar,baz,foo,qux,'},
    {'add_tags': ['foo,baz,', 'bar,'], 'tag': ['+', 'baz,qux'],
     'tags_fetch': False, 'tags_in': ',bar,baz,foo,qux,'},
    {'add_tags': ['-', 'foo,baz,bar,'], 'tag': ['baz,', 'qux,'],
     'tags_fetch': False, 'tags_in': ',baz,qux,', 'tags_except': ',bar,baz,foo,'},
    {'add_tags': ['foo,baz,', 'bar,'], 'tag': ['-', 'baz,qux'],
     'tags_fetch': False, 'tags_in': ',bar,baz,foo,', 'tags_except': ',baz,qux,'},
    {'add_tags': ['-', 'foo,baz,bar,'], 'tag': ['-', 'baz,', 'qux,'], 'tags_except': ',bar,baz,foo,qux,'},
    {'add_tags': ['-', 'foo,baz,', 'bar,'], 'tag': ['+', 'baz,', 'qux,'],
     'tags_in': ',baz,qux,', 'tags_except': ',bar,baz,foo,'},
    {'add_tags': ['+', 'foo,baz,', 'bar,'], 'tag': ['-', 'baz,', 'qux,'],
     'tags_in': ',bar,baz,foo,', 'tags_except': ',baz,qux,'},
])
def test_add(stdin, bdb, prompt, value_params, fetch_params):
    _test_add(bdb, prompt, **value_params, **fetch_params)

def _test_add(bdb, prompt, *, add_tags=[], tag=[], tags_fetch=True, tags_in=None, tags_except=None,
              title=None, comment=None, immutable=None, offline=False, url_redirect=False,
              tag_redirect=False, tag_error=False, del_range=None, del_error=None):
    argv = ['--add', (url := 'https://example.com/')] + add_tags
    if tag:
        argv += ['--tag'] + tag
    if title is not None:
        argv += ['--title', title]
    if comment is not None:
        argv += ['--comment', comment]
    if immutable is not None:
        argv += ['--immutable', str(int(immutable))]
    if offline:
        argv += ['--offline']
    if url_redirect:
        argv += ['--url-redirect']
    if tag_redirect:
        argv += ['--tag-redirect'] + ([] if isinstance(tag_redirect, bool) else [tag_redirect])
    if tag_error:
        argv += ['--tag-error'] + ([] if isinstance(tag_error, bool) else [tag_error])
    if del_error:
        argv += ['--del-error'] + del_range
    with pytest.raises(SystemExit):
        buku.main(argv)
    network_test = url_redirect or tag_redirect or tag_error or del_error
    fetch = not offline and (network_test or tags_fetch or title is None)
    bdb.add_rec.assert_called_with(
        url, title, tags_in, comment, immutable, delay_commit=False, fetch=fetch,
        tags_fetch=tags_fetch, tags_except=tags_except, url_redirect=url_redirect,
        tag_redirect=tag_redirect, tag_error=tag_error, del_error=del_error)
    bdb.searchdb.assert_not_called()
    prompt.assert_not_called()
    bdb.close_quit.assert_called_with(0)
