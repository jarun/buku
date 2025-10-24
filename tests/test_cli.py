from unittest import mock
from io import StringIO
import os
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

@pytest.mark.parametrize('nostdin', [True, False])
@pytest.mark.parametrize('db', [None, './foo.db'])
def test_prompt(BukuDb, bdb, piped_input, prompt, nostdin, db):
    argv = (['--nostdin'] if nostdin else []) + (['--db', db] if db else [])
    BukuDb.get_default_dbdir.return_value = '/default/db/dir'
    with pytest.raises(SystemExit):
        buku.main(argv)
    if argv and argv[0] != '--nostdin':
        piped_input.assert_called_with(argv, [])
    else:
        piped_input.assert_not_called()
    BukuDb.assert_called_with(dbfile=db or os.path.join('/default/db/dir', 'bookmarks.db'), default_scheme=buku.SCHEME_HTTP)
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
    print(argv)
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


@pytest.mark.parametrize('np', [{}, {'np': []}])
@pytest.mark.parametrize('count', [{}, {'count': ['10']}])
@pytest.mark.parametrize('order, indices, command', [
    (['tags', '-netloc', '+url'], None, {'order': ['tags,-netloc,+url'], 'print': []}),
    (['-description', '+uri'], [5, 8, 9, 10, 11, 12, 40, 41, 42],
     {'order': [',-description', '+uri'], 'print': ['5', '8-12', '-3']}),
])
def test_order_print(bdb, stdin, prompt, order, indices, command, count, np):
    command = dict(command, **count, **np)
    argv = [s for k, v in command.items() for s in ([f'--{k}'] + v)]
    print(argv)
    result = [None] * 20
    bdb.list_using_id.return_value = result
    bdb.get_max_id.return_value = 42
    with pytest.raises(SystemExit):
        buku.main(argv)
    bdb.get_max_id.assert_called_with()
    if not (_count := command.get('count')):
        bdb.print_rec.assert_called_with(indices, order=order)
    else:
        if not command['print']:
            bdb.list_using_id.assert_called_with(order=order)
        else:
            bdb.list_using_id.assert_called_with(command['print'], order=order)
        prompt.assert_called_with(bdb, result, noninteractive=('np' in command), num=int(_count[0]), order=order)

@pytest.mark.parametrize('search', ['', 'sany', 'sall', 'sreg', 'stag'])
@pytest.mark.parametrize('exclude', [None, ['xyzzy', 'grue']])
@pytest.mark.parametrize('keywords, rest', [
    ([], {}),
    (['foo', 'bar'], {'markers': []}),
    (['foo', 'bar'], {'deep': []}),
    (['foo', 'bar'], {'stag': ['baz', 'qux']})
])
def test_order_search(bdb, stdin, prompt, search, exclude, keywords, rest):
    if (search == '' and not keywords) or (search == 'stag' and 'stag' in rest):
        pytest.skip('Invalid combination')
    order, stag, deep, markers = ['title', '-index'], rest.get('stag'), 'deep' in rest, 'markers' in rest
    argv = ([] if search == '' else [f'--{search}']) + keywords + ['--order', ','.join(order)]
    argv += [s for k, v in rest.items() for s in ([f'--{k}'] + v)] + ([] if not exclude else ['--exclude'] + exclude)
    bdb.search_by_tag.return_value = ['tag search results']
    with pytest.raises(SystemExit):
        buku.main(argv)
    if search == 'stag':
        if not keywords:
            prompt.assert_called_with(bdb, None, noninteractive=False, listtags=True, suggest=False, order=order)
        else:
            bdb.search_by_tag.assert_called_with(' '.join(keywords), order=order)
            bdb.exclude_results_from_search.assert_called_with(
                bdb.search_by_tag.return_value, exclude, deep=deep, markers=markers)
    if search == 'stag' or not keywords:
        bdb.search_keywords_and_filter_by_tags.assert_not_called()
    elif search in ('', 'sany'):
        bdb.search_keywords_and_filter_by_tags.assert_called_with(
            keywords, deep=deep, stag=stag, markers=markers, without=exclude, order=order)
    elif search == 'sall':
        bdb.search_keywords_and_filter_by_tags.assert_called_with(
            keywords, all_keywords=True, deep=deep, stag=stag, markers=markers, without=exclude, order=order)
    elif search == 'sreg':
        bdb.search_keywords_and_filter_by_tags.assert_called_with(
            keywords, regex=True, stag=stag, markers=markers, without=exclude, order=order)

@pytest.mark.parametrize('json', [None, '', 'output.json'])
@pytest.mark.parametrize('indices', [None, '', '1-10', '-10'])  # None = search
@pytest.mark.parametrize('random', [None, 1, 3])
@mock.patch('random.sample', return_value='sampled')
@mock.patch('buku.print_rec_with_filter')
@mock.patch('buku.write_string_to_file')
@mock.patch('buku.format_json', return_value='formatted')
@mock.patch('buku.print_json_safe')
def test_random(_print_json_safe, _format_json, _write_string_to_file, _print_rec_with_filter, _sample,
                bdb, stdin, prompt, random, indices, json):
    wrap = mock.Mock()
    wrap.attach_mock(_sample, 'random_sample')
    wrap.attach_mock(_print_rec_with_filter, 'print_rec_with_filter')
    wrap.attach_mock(_write_string_to_file, 'write_string_to_file')
    wrap.attach_mock(_format_json, 'format_json')
    wrap.attach_mock(_print_json_safe, 'print_json_safe')
    wrap.attach_mock(prompt, 'prompt')
    wrap.attach_mock(bdb, 'bdb')
    bdb.get_max_id.return_value = 42
    bdb._sort.return_value = 'sorted'
    bdb.search_keywords_and_filter_by_tags.return_value = 'found'
    argv = (['--sall', 'foo'] if indices is None else ['--print'] + ([] if not indices else [indices]))
    argv += ([] if json is None else ['--json'] + ([] if not json else [json]))
    argv += ([] if not random else ['--random'] + ([] if random == 1 else [str(random)]))
    with pytest.raises(SystemExit):
        buku.main(argv)
    calls = ([] if indices is None else [mock.call.bdb.get_max_id()])
    if indices:                # --print 1-10
        idxs = list(range(33, 43) if indices == '-10' else range(1, 11))
        calls += ([mock.call.bdb.print_rec(idxs, order=[])] if not random else
                  [mock.call.random_sample(idxs, random),
                   mock.call.bdb.print_rec('sampled', order=[])])
    elif indices is not None:  # --print
        calls += ([mock.call.bdb.print_rec(None, order=[])] if not random else
                  [mock.call.random_sample(range(1, 43), random),
                   mock.call.bdb.print_rec('sampled', order=[])])
    else:                      # --sall foo
        calls += [mock.call.bdb.search_keywords_and_filter_by_tags(
                      ['foo'], all_keywords=True, deep=False, stag=None, markers=False, without=None, order=[])]
        if random:
            calls += [mock.call.random_sample('found', random),
                      mock.call.bdb._sort('sampled', [])]
        res = ('sorted' if random else 'found')
        if json:
            calls += [mock.call.format_json(res, (random == 1), field_filter=0),
                      mock.call.write_string_to_file('formatted', json)]
        elif json is not None:
            calls += [mock.call.print_json_safe(res, (random == 1), field_filter=0)]
        elif random:
            calls += [mock.call.print_rec_with_filter(res, field_filter=0)]
        else:
            calls += [mock.call.prompt(bdb, res, noninteractive=False, deep=False, markers=False, order=[], num=10)]
    calls += [mock.call.bdb.close_quit(0)]
    assert wrap.mock_calls == calls

@pytest.mark.parametrize('search', [True, False])
@pytest.mark.parametrize('random', [None, 1, 3])
@mock.patch('random.sample', return_value='sampled')
@mock.patch('buku.print_rec_with_filter')
def test_random_export(_print_rec_with_filter, _sample, bdb, stdin, prompt, random, search):
    wrap = mock.Mock()
    wrap.attach_mock(_sample, 'random_sample')
    wrap.attach_mock(_print_rec_with_filter, 'print_rec_with_filter')
    wrap.attach_mock(prompt, 'prompt')
    wrap.attach_mock(bdb, 'bdb')
    bdb.get_max_id.return_value = 42
    bdb._sort.return_value = 'sorted'
    bdb.search_keywords_and_filter_by_tags.return_value = 'found'
    argv = ['--export', 'export.md'] + ([] if not search else ['--sall', 'foo'])
    argv += ([] if not random else ['--random'] + ([] if random == 1 else [str(random)]))
    with pytest.raises(SystemExit):
        buku.main(argv)
    calls = []
    if not search:
        calls += [mock.call.bdb.exportdb('export.md', order=[], pick=random)]
    else:
        calls += [mock.call.bdb.search_keywords_and_filter_by_tags(
                      ['foo'], all_keywords=True, deep=False, stag=None, markers=False, without=None, order=[])]
        if random:
            calls += [mock.call.random_sample('found', random),
                      mock.call.bdb._sort('sampled', [])]
        res = ('sorted' if random else 'found')
        if random:
            calls += [mock.call.print_rec_with_filter(res, field_filter=0)]
        else:
            calls += [mock.call.prompt(bdb, res, noninteractive=True, deep=False, markers=False, order=[], num=10)]
        calls += [mock.call.bdb.exportdb('export.md', res)]
    calls += [mock.call.bdb.close_quit(0)]
    assert wrap.mock_calls == calls


@pytest.mark.parametrize('db', [None, './foo.db', 'bar.sqlite', 'name'])
@pytest.mark.parametrize('action', ['print', 'lock', 'unlock'])
@mock.patch('buku.BukuCrypt')
def test_custom_db(_BukuCrypt, BukuDb, stdin, db, action):
    wrap = mock.Mock()
    wrap.attach_mock(BukuDb, 'BukuDb')
    wrap.attach_mock(BukuDb.return_value, 'bdb')
    wrap.attach_mock(_BukuCrypt, 'BukuCrypt')
    BukuDb.return_value.get_max_id.return_value = None
    BukuDb.get_default_dbdir.return_value = '/default/db/dir'
    _db = (db if db != 'name' else '/default/db/dir/name.db')
    argv = ['--nostdin'] + ([] if not db else ['--db', db]) + [f'--{action}']
    with pytest.raises(SystemExit):
        buku.main(argv)
    calls = []
    if db == 'name':
        calls += [mock.call.BukuDb.get_default_dbdir()]
    if action == 'lock':
        calls += [mock.call.BukuCrypt.encrypt_file(8, dbfile=_db)]
    else:
        if action == 'unlock':
            calls += [mock.call.BukuCrypt.decrypt_file(8, dbfile=_db)]
        calls += [mock.call.BukuDb(None, 0, True, dbfile=_db, colorize=True, default_scheme=buku.SCHEME_HTTP)]
        if action == 'print':
            calls += [mock.call.bdb.get_max_id(),
                      mock.call.bdb.print_rec(None, order=[])]
        calls += [mock.call.bdb.close_quit(0)]
    assert wrap.mock_calls == calls
