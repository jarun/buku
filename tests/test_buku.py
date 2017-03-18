"""test module."""
from itertools import product
from unittest import mock
import os
import signal
import sys
import unittest

import pytest

from buku import is_int, parse_tags

only_python_3_5 = pytest.mark.skipif(sys.version_info < (3, 5), reason="requires python3.5")


@pytest.mark.parametrize(
    'url, exp_res',
    [
        ('http://example.com', False),
    ]
)
def test_is_bad_url(url, exp_res):
    """test func."""
    import buku
    assert exp_res == buku.is_bad_url(url)


@pytest.mark.parametrize(
    'url, exp_res',
    [
        ('http://example.com/file.pdf', True),
        ('http://example.com/file.txt', True),
        ('http://example.com/file.jpg', False),
    ]
)
def test_is_ignored_mime(url, exp_res):
    """test func."""
    import buku
    assert exp_res == buku.is_ignored_mime(url)


def test_get_page_title():
    """test func."""
    resp = mock.Mock()
    parser = mock.Mock()
    with mock.patch('buku.BukuHTMLParser', return_value=parser):
        import buku
        res = buku.get_page_title(resp)
        assert res == parser.parsed_title


def test_gen_headers():
    """test func."""
    import buku
    exp_myheaders = {
        'Accept-Encoding': 'gzip,deflate',
        'User-Agent': buku.USER_AGENT,
        'Accept': '*/*',
        'Cookie': '',
        'DNT': '1'
    }
    buku.gen_headers()
    assert buku.myproxy is None
    assert buku.myheaders == exp_myheaders


@pytest.mark.parametrize('m_myproxy', [None, mock.Mock()])
def test_get_PoolManager(m_myproxy):
    """test func."""
    with mock.patch('buku.urllib3') as m_ul3:
        import buku
        buku.myproxy = m_myproxy
        res = buku.get_PoolManager()
        if m_myproxy:
            m_ul3.ProxyManager.assert_called_once_with(
                m_myproxy, num_pools=1, headers=buku.myheaders)
            assert res == m_ul3.ProxyManager.return_value
        else:
            m_ul3.PoolManager.assert_called_once_with(
                num_pools=1, headers=buku.myheaders)
            assert res == m_ul3.PoolManager.return_value


@pytest.mark.parametrize(
    'keywords, exp_res',
    [
        (None, None),
        ([], None),
        (['tag1', 'tag2'], ',tag1 tag2,'),
        (['tag1,tag2', 'tag3'], ',tag1,tag2 tag3,'),
    ]
)
def test_parse_tags(keywords, exp_res):
    """test func."""
    import buku
    if keywords is None:
        pass
    elif not keywords:
        exp_res = buku.DELIM
    res = buku.parse_tags(keywords)
    assert res == exp_res


@pytest.mark.parametrize(
    'nav, is_editor_valid_retval, edit_rec_retval',
    product(
        ['w', [None, None, 1], [None, None, 'string']],
        [True, False],
        [[mock.Mock(), mock.Mock(), mock.Mock(), mock.Mock()], None]
    )
)
def test_edit_at_prompt(nav, is_editor_valid_retval, edit_rec_retval):
    """test func."""
    obj = mock.Mock()
    editor = mock.Mock()
    with mock.patch('buku.get_system_editor', return_value=editor), \
            mock.patch('buku.is_editor_valid', return_value=is_editor_valid_retval), \
            mock.patch('buku.edit_rec', return_value=edit_rec_retval) as m_edit_rec:
        import buku
        buku.edit_at_prompt(obj, nav)
        # test
        if nav == 'w' and not is_editor_valid_retval:
            return
        elif nav == 'w':
            m_edit_rec.assert_called_once_with(editor, '', None, buku.DELIM, None)
        elif buku.is_int(nav[2:]):
            obj.edit_update_rec.assert_called_once_with(int(nav[2:]))
            return
        else:
            editor = nav[2:]
        m_edit_rec.assert_called_once_with(editor, '', None, buku.DELIM, None)
        if edit_rec_retval is not None:
            obj.add_rec(*edit_rec_retval)


@only_python_3_5
@pytest.mark.parametrize(
    'idx, row0, row1, row2, row3, row4, row5',
    product(
        [0, 1],
        [0],
        ['', 'row1'],
        ['', 'row2'],
        [',', 'row3'],
        ['', 'row4'],
        [0, 1],
    )
)
def test_print_record(idx, row0, row1, row2, row3, row4, row5):
    """test func."""
    row = [row0, row1, row2, row3, row4, row5]
    pr = None
    with mock.patch('buku.print') as m_print:
        import buku
        buku.print_record(row, idx)

        if idx != 0:
            pr = buku.ID_str % (idx, row1, row0)
        else:
            pr = buku.ID_DB_str % (row0, row1)
            if row5 & 1:
                pr = buku.MUTE_str % (pr)
            else:
                pr += '\n'

        if row2 != '':
            pr = buku.TITLE_str % (pr, row2)
        if row4 != '':
            pr = buku.DESC_str % (pr, row4)
        if row3 != buku.DELIM:
            pr = buku.TAG_str % (pr, row3[1:-1])

        m_print.assert_called_once_with(pr)


@pytest.mark.parametrize(
    'field_filter, single_record',
    product(range(4), [True, False])
)
def test_format_json(field_filter, single_record):
    """test func."""
    resultset = [['row{}'.format(x) for x in range(5)]]
    if field_filter == 1:
        marks = {'uri': 'row1'}
    elif field_filter == 2:
        marks = {'uri': 'row1', 'tags': 'row3'[1:-1]}
    elif field_filter == 3:
        marks = {'title': 'row2'}
    else:
        marks = {
            'index': 'row0',
            'uri': 'row1',
            'title': 'row2',
            'description': 'row4',
            'tags': 'row3'[1:-1]
        }
    if not single_record:
        marks = [marks]

    with mock.patch('buku.json') as m_json:
        import buku
        res = buku.format_json(resultset, single_record, field_filter)
        m_json.dumps.assert_called_once_with(marks, sort_keys=True, indent=4)
        assert res == m_json.dumps.return_value


@pytest.mark.parametrize(
    'string, exp_res',
    [
        ('string', False),
        ('12', True),
        ('12.1', False),
    ]
)
def test_is_int(string, exp_res):
    """test func."""
    import buku
    assert exp_res == buku.is_int(string)


@pytest.mark.parametrize(
    'url, opened_url',
    [
        ['http://example.com', 'http://example.com', ],
        ['example.com', 'http://example.com', ],
    ]
)
def test_browse(url, opened_url):
    """test func."""
    with mock.patch('buku.webbrowser') as m_webbrowser:
        import buku
        buku.browse(url)
        m_webbrowser.open.assert_called_once_with(opened_url)


@only_python_3_5
@pytest.mark.parametrize(
    'status_code, latest_release',
    product([200, 404], [True, False])
)
def test_check_upstream_release(status_code, latest_release):
    """test func."""
    resp = mock.Mock()
    resp.status_code = status_code
    with mock.patch('buku.requests') as m_requests, \
            mock.patch('buku.print') as m_print:
        import buku
        if latest_release:
            latest_version = 'v{}'.format(buku.__version__)
        else:
            latest_version = 'v0'
        resp.json.return_value = [{'tag_name': latest_version}]
        m_requests.get.return_value = resp
        buku.check_upstream_release()
        if status_code != 200:
            return
        if latest_release:
            print_text = 'This is the latest release'
        else:
            print_text = 'Latest upstream release is %s' % latest_version
        m_print.assert_called_once_with(print_text)


@pytest.mark.parametrize(
    'exp, item, exp_res',
    [
        ('cat.y', 'catty', True),
        ('cat.y', 'caty', False),
    ]
)
def test_regexp(exp, item, exp_res):
    """test func."""
    import buku
    res = buku.regexp(exp, item)
    assert res == exp_res


@pytest.mark.parametrize('token, exp_res', [('text', ',text,')])
def test_delim_wrap(token, exp_res):
    """test func."""
    import buku
    res = buku.delim_wrap(token)
    assert res == exp_res


@only_python_3_5
def test_read_in():
    """test func."""
    message = mock.Mock()
    with mock.patch('buku.disable_sigint_handler'), \
            mock.patch('buku.enable_sigint_handler'), \
            mock.patch('buku.input', return_value=message):
        import buku
        res = buku.read_in(msg=mock.Mock())
        assert res == message


def test_sigint_handler_with_mock():
    """test func."""
    with mock.patch('buku.os') as m_os:
        import buku
        buku.sigint_handler(mock.Mock(), mock.Mock())
        m_os._exit.assert_called_once_with(1)


def test_get_system_editor():
    """test func."""
    with mock.patch('buku.os') as m_os:
        import buku
        res = buku.get_system_editor()
        assert res == m_os.environ.get.return_value
        m_os.environ.get.assert_called_once_with('EDITOR', 'none')


@pytest.mark.parametrize(
    'editor, exp_res',
    [
        ('none', False),
        ('0', False),
        ('random_editor', True),
    ]
)
def test_is_editor_valid(editor, exp_res):
    """test func."""
    import buku
    assert buku.is_editor_valid(editor) == exp_res


@pytest.mark.parametrize(
    'url, title_in, tags_in, desc',
    product(
        [None, 'example.com'],
        [None, '', 'title'],
        ['', 'tag1,tag2', ',tag1,tag2,'],
        [None, '', 'description'],
    )
)
def test_to_temp_file_content(url, title_in, tags_in, desc):
    """test func."""
    import buku
    res = buku.to_temp_file_content(url, title_in, tags_in, desc)
    lines = [
        '# Lines beginning with "#" will be stripped.',
        '# Add URL in next line (single line).',
        '# Add TITLE in next line (single line). Leave blank to web fetch, "-" for no title.',
        '# Add comma-separated TAGS in next line (single line).',
        '# Add COMMENTS in next line(s).',
    ]
    idx_offset = 0
    # url
    if url is not None:
        lines.insert(2, url)
        idx_offset += 1
    if title_in is None:
        title_in = ''
    elif title_in == '':
        title_in = '-'
    else:
        pass

    # title
    lines.insert(idx_offset + 3, title_in)
    idx_offset += 1

    # tags
    lines.insert(idx_offset + 4, tags_in.strip(buku.DELIM))
    idx_offset += 1

    # description
    if desc is not None and desc != '':
        pass
    else:
        desc = ''
    lines.insert(idx_offset + 5, desc)

    for idx, res_line in enumerate(res.splitlines()):
        assert lines[idx] == res_line


@pytest.mark.parametrize(
    'content, exp_res',
    [
        ('', None),
        ('#line1\n#line2', None),
        (
            '\n'.join([
                'example.com',
                'title',
                'tags',
                'desc',
            ]),
            ('example.com', 'title', ',tags,', 'desc')
        )
    ]
)
def test_parse_temp_file_content(content, exp_res):
    """test func."""
    import buku
    res = buku.parse_temp_file_content(content)
    assert res == exp_res


@only_python_3_5
@pytest.mark.skip(reason="can't patch subprocess")
def test_edit_rec():
    """test func."""
    editor = 'nanoe'
    args = ('url', 'title_in', 'tags_in', 'desc')
    with mock.patch('buku.to_temp_file_content'), \
            mock.patch('buku.os'), \
            mock.patch('buku.open'), \
            mock.patch('buku.parse_temp_file_content') as m_ptfc:
        import buku
        res = buku.edit_rec(editor, *args)
        assert res == m_ptfc.return_value


@pytest.mark.parametrize('argv, pipeargs, isatty', product(['argv'], [None, []], [True, False]))
def test_piped_input(argv, pipeargs, isatty):
    """test func."""
    with mock.patch('buku.sys') as m_sys:
        m_sys.stdin.isatty.return_value = isatty
        m_sys.stdin.readlines.return_value = 'arg1\narg2'
        import buku
        if pipeargs is None and not isatty:
            with pytest.raises(TypeError):
                buku.piped_input(argv, pipeargs)
            return
        buku.piped_input(argv, pipeargs)


class TestHelpers(unittest.TestCase):

    # @unittest.skip('skipping')
    def test_parse_tags(self):
        # call with None
        parsed = parse_tags(None)
        self.assertIsNone(parsed)
        # call with empty list
        parsed = parse_tags([])
        self.assertEqual(parsed, ",")
        # empty tags
        parsed = parse_tags([",,,,,"])
        self.assertEqual(parsed, ",")
        # sorting tags
        parsed = parse_tags(["z_tag,a_tag,n_tag"])
        self.assertEqual(parsed, ",a_tag,n_tag,z_tag,")
        # whitespaces
        parsed = parse_tags([" a tag , ,   ,  ,\t,\n,\r,\x0b,\x0c"])
        self.assertEqual(parsed, ",a tag,")
        # duplicates, excessive spaces
        parsed = parse_tags(["tag,tag, tag,  tag,tag , tag "])
        self.assertEqual(parsed, ",tag,")
        # escaping quotes
        parsed = parse_tags(["\"tag\",\'tag\',tag"])
        self.assertEqual(parsed, ",\"tag\",\'tag\',tag,")
        # combo
        parsed = parse_tags([",,z_tag, a tag ,\t,,,  ,n_tag ,n_tag, a_tag, \na tag  ,\r, \"a_tag\""])
        self.assertEqual(parsed, ",\"a_tag\",a tag,a_tag,n_tag,z_tag,")

    # @unittest.skip('skipping')
    def test_is_int(self):
        self.assertTrue(is_int('0'))
        self.assertTrue(is_int('1'))
        self.assertTrue(is_int('-1'))
        self.assertFalse(is_int(''))
        self.assertFalse(is_int('one'))

# This test fails because we use os._exit() now
@unittest.skip('skipping')
def test_sigint_handler(capsys):
    try:
        # sending SIGINT to self
        os.kill(os.getpid(), signal.SIGINT)
    except SystemExit as error:
        out, err = capsys.readouterr()
        # assert exited with 1
        assert error.args[0] == 1
        # assert proper error message
        assert out == ''
        assert err == "\nInterrupted.\n"
