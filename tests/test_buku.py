"""test module."""
from itertools import product
from unittest import mock
from urllib.parse import urlparse
import json
import logging
import os
import signal
import sys
import unittest

import pytest

from buku import is_int, parse_tags, prep_tag_search

only_python_3_5 = pytest.mark.skipif(
    sys.version_info < (3, 5), reason="requires Python 3.5 or later")


@pytest.mark.parametrize(
    'url, exp_res',
    [
        ['http://example.com', False],
        ['ftp://ftp.somedomain.org', False],
        ['http://examplecom.', True],
        ['http://.example.com', True],
        ['http://example.com.', True],
        ['about:newtab', True],
        ['chrome://version/', True],
    ]
)
def test_is_bad_url(url, exp_res):
    """test func."""
    import buku
    res = buku.is_bad_url(url)
    assert res == exp_res


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
    assert buku.MYPROXY is None
    assert buku.MYHEADERS == exp_myheaders


@pytest.mark.parametrize('m_myproxy', [None, mock.Mock()])
def test_get_PoolManager(m_myproxy):
    """test func."""
    with mock.patch('buku.urllib3'):
        import buku
        buku.myproxy = m_myproxy
        assert buku.get_PoolManager()


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
    'records, field_filter, exp_res',
    [
        [
            [(1, 'http://url1.com', 'title1', ',tag1,'),
             (2, 'http://url2.com', 'title2', ',tag1,tag2,')],
            1,
            ['1\thttp://url1.com', '2\thttp://url2.com']
        ],
        [
            [(1, 'http://url1.com', 'title1', ',tag1,'),
             (2, 'http://url2.com', 'title2', ',tag1,tag2,')],
            2,
            ['1\thttp://url1.com\ttag1', '2\thttp://url2.com\ttag1,tag2']
        ],
        [
            [(1, 'http://url1.com', 'title1', ',tag1,'),
             (2, 'http://url2.com', 'title2', ',tag1,tag2,')],
            3,
            ['1\ttitle1', '2\ttitle2']
        ],
        [
            [(1, 'http://url1.com', 'title1', ',tag1,'),
             (2, 'http://url2.com', 'title2', ',tag1,tag2,')],
            4,
            ['1\thttp://url1.com\ttitle1\ttag1', '2\thttp://url2.com\ttitle2\ttag1,tag2']
        ],
        [
            [(1, 'http://url1.com', 'title1', ',tag1,'),
             (2, 'http://url2.com', 'title2', ',tag1,tag2,')],
            10,
            ['http://url1.com', 'http://url2.com']
        ],
        [
            [(1, 'http://url1.com', 'title1', ',tag1,'),
             (2, 'http://url2.com', 'title2', ',tag1,tag2,')],
            20,
            ['http://url1.com\ttag1', 'http://url2.com\ttag1,tag2']
        ],
        [
            [(1, 'http://url1.com', 'title1', ',tag1,'),
             (2, 'http://url2.com', 'title2', ',tag1,tag2,')],
            30,
            ['title1', 'title2']
        ],
        [
            [(1, 'http://url1.com', 'title1', ',tag1,'),
             (2, 'http://url2.com', 'title2', ',tag1,tag2,')],
            40,
            ['http://url1.com\ttitle1\ttag1', 'http://url2.com\ttitle2\ttag1,tag2']
        ]
    ]
)
def test_print_rec_with_filter(records, field_filter, exp_res):
    """test func."""
    with mock.patch('buku.print', create=True) as m_print:
        import buku
        buku.print_rec_with_filter(records, field_filter)
        for res in exp_res:
            m_print.assert_any_call(res)


@pytest.mark.parametrize(
    'taglist, exp_res',
    [
        [
            'tag1, tag2+3',
            ([',tag1,', ',tag2+3,'], 'OR', None)
        ],
        [
            'tag1 + tag2-3 + tag4',
            ([',tag1,', ',tag2-3,', ',tag4,'], 'AND', None)
        ],
        [
            'tag1, tag2-3 - tag4, tag5',
            ([',tag1,', ',tag2-3,'], 'OR', ',tag4,|,tag5,')
        ]
    ]
)
def test_prep_tag_search(taglist, exp_res):
    """test prep_tag_search helper function"""

    results = prep_tag_search(taglist)
    assert results == exp_res


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
        if nav == 'w':
            m_edit_rec.assert_called_once_with(editor, '', None, buku.DELIM, None)
        elif buku.is_int(nav[2:]):
            obj.edit_update_rec.assert_called_once_with(int(nav[2:]))
            return
        else:
            editor = nav[2:]
        m_edit_rec.assert_called_once_with(editor, '', None, buku.DELIM, None)
        if edit_rec_retval is not None:
            obj.add_rec(*edit_rec_retval)


@pytest.mark.parametrize(
    'field_filter, single_record',
    product(list(range(4)), [True, False])
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
    'url, opened_url, platform',
    [
        ['http://example.com', 'http://example.com', 'linux'],
        ['example.com', 'http://example.com', 'linux'],
        ['http://example.com', 'http://example.com', 'win32'],
    ]
)
def test_browse(url, opened_url, platform):
    """test func."""
    with mock.patch('buku.webbrowser') as m_webbrowser, \
            mock.patch('buku.sys') as m_sys, \
            mock.patch('buku.os'):
        m_sys.platform = platform
        get_func_retval = mock.Mock()
        m_webbrowser.get.return_value = get_func_retval
        import buku
        buku.browse.suppress_browser_output = True
        buku.browse.override_text_browser = False
        buku.browse(url)
        if platform == 'win32':
            m_webbrowser.open.assert_called_once_with(opened_url, new=2)
        else:
            get_func_retval.open.assert_called_once_with(opened_url, new=2)


@only_python_3_5
@pytest.mark.parametrize(
    'status_code, latest_release',
    product([200, 404], [True, False])
)
def test_check_upstream_release(status_code, latest_release):
    """test func."""
    resp = mock.Mock()
    resp.status = status_code
    m_manager = mock.Mock()
    m_manager.request.return_value = resp
    with mock.patch('buku.urllib3') as m_urllib3, \
            mock.patch('buku.print') as m_print:
        import buku
        if latest_release:
            latest_version = 'v{}'.format(buku.__version__)
        else:
            latest_version = 'v0'
        m_urllib3.PoolManager.return_value = m_manager
        resp.data.decode.return_value = json.dumps([{'tag_name': latest_version}])
        buku.check_upstream_release()
        if status_code != 200:
            return
        len(m_print.mock_calls) == 1


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
        [None, '', '-', 'tag1,tag2', ',tag1,tag2,', ',,,,,'],
        [None, '', '-', 'description'],
    )
)
def test_to_temp_file_content(url, title_in, tags_in, desc):
    """test func."""
    import buku
    if desc is None:
        desc_text = '\n'
    elif desc == '':
        desc_text = '-'
    else:
        desc_text = desc
    if title_in is None:
        title_text = ''
    elif title_in == '':
        title_text = '-'
    else:
        title_text = title_in
    if tags_in is None:
        with pytest.raises(AttributeError):
            res = buku.to_temp_file_content(url, title_in, tags_in, desc)
        return
    res = buku.to_temp_file_content(url, title_in, tags_in, desc)
    lines = """# Lines beginning with "#" will be stripped.
# Add URL in next line (single line).{}
# Add TITLE in next line (single line). Leave blank to web fetch, "-" for no title.{}
# Add comma-separated TAGS in next line (single line).{}
# Add COMMENTS in next line(s). Leave blank to web fetch, "-" for no comments.{}""".format(
        ''.join(['\n', url]) if url is not None else '',
        ''.join(['\n', title_text]),
        ''.join(['\n', ','.join([x for x in tags_in.split(',') if x])]) if tags_in else '\n',
        ''.join(['\n', desc_text])
    )
    assert res == lines


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


@pytest.mark.parametrize(
    'url, exp_res',
    [
        ['http://example.com.', (None, None, None, 0, 1)],
        ['http://example.com', ('Example Domain', None, None, 0, 0)],
        ['http://example.com/page1.txt', (('', '', '', 1, 0))],
        ['about:new_page', ((None, None, None, 0, 1))],
        ['chrome://version/', ((None, None, None, 0, 1))],
        ['chrome://version/', ((None, None, None, 0, 1))],
        # [
        #     'http://4pda.ru/forum/index.php?showtopic=182463&st=1640#entry6044923',
        #     (
        #         'Samsung GT-I5800 Galaxy 580 - Обсуждение - 4PDA',
        #         'Samsung GT-I5800 Galaxy 580 - Обсуждение - 4PDA',
        #         None,
        #         0, 0
        #     )
        # ],
        [
            'https://www.google.ru/search?'
            'newwindow=1&safe=off&q=xkbcomp+alt+gr&'
            'oq=xkbcomp+alt+gr&'
            'gs_l=serp.3..33i21.28976559.28977886.0.'
            '28978017.6.6.0.0.0.0.167.668.0j5.5.0....0...1c.1.64.'
            'serp..1.2.311.06cSKPTLo18',
            ('xkbcomp alt gr', None, None, 0, 0)
        ],
        [
            'http://www.vim.org/scripts/script.php?script_id=4641',
            (
                'mlessnau_case - "in-case" selection, deletion and substitution '
                'for underscore, camel, mixed case : vim online',
                None, None, 0, 0
            )
        ],
    ]
)
def test_network_handler_with_url(url, exp_res):
    """test func."""
    import buku
    import urllib3
    buku.urllib3 = urllib3
    buku.myproxy = None
    res = buku.network_handler(url)
    if urlparse(url).netloc == 'www.google.ru':
        temp_res = [res[0].split(" - ")[0], ]
        temp_res.extend(res[1:])
        res = tuple(temp_res)
    assert res == exp_res


@pytest.mark.parametrize(
    'url, exp_res',
    [
        ('http://example.com', False),
        ('apt:package1,package2,package3', True),
        ('apt://firefox', True),
        ('file:///tmp/vim-markdown-preview.html', True),
        ('place:sort=8&maxResults=10', True),
    ]
)
def test_is_nongeneric_url(url, exp_res):
    import buku
    res = buku.is_nongeneric_url(url)
    assert res == exp_res


@pytest.mark.parametrize(
    'newtag, exp_res',
    [
        (None, ('http://example.com', 'text1', ',', None, 0, True)),
        ('tag1', ('http://example.com', 'text1', ',tag1,', None, 0, True)),
    ]
)
def test_import_md(tmpdir, newtag, exp_res):
    from buku import import_md
    p = tmpdir.mkdir("importmd").join("test.md")
    p.write("[text1](http://example.com)")
    res = list(import_md(p.strpath, newtag))
    assert res[0] == exp_res

@pytest.mark.parametrize(
    'newtag, exp_res',
    [
        (None, ('http://example.com', 'text1', ',tag1,:tag2,tag:3,tag4:,tag::5,tag:6:,', None, 0, True)),
        ('tag0', ('http://example.com', 'text1', ',tag0,tag1,:tag2,tag:3,tag4:,tag::5,tag:6:,', None, 0, True)),
    ]
)
def test_import_org(tmpdir, newtag, exp_res):
    from buku import import_org
    p = tmpdir.mkdir("importorg").join("test.org")
    p.write("[[http://example.com][text1]] :tag1: ::tag2:tag::3:tag4:: :tag:::5:tag::6:: :")
    res = list(import_org(p.strpath, newtag))
    assert res[0] == exp_res


@pytest.mark.parametrize(
    'html_text, exp_res',
    [
        (
            """<DT><A HREF="https://github.com/j" ADD_DATE="1360951967" PRIVATE="1" TAGS="tag1,tag2">GitHub</A>
<DD>comment for the bookmark here
<a> </a>""",
            ((
                'https://github.com/j', 'GitHub', ',tag1,tag2,',
                'comment for the bookmark here', 0, True, False
            ),)
        ),
        (
            """DT><A HREF="https://github.com/j" ADD_DATE="1360951967" PRIVATE="1" TAGS="tag1,tag2">GitHub</A>
            <DD>comment for the bookmark here
            <a>second line of the comment here</a>""",
            ((
                'https://github.com/j', 'GitHub', ',tag1,tag2,',
                'comment for the bookmark here', 0, True, False
            ),)
        ),
        (
            """DT><A HREF="https://github.com/j" ADD_DATE="1360951967" PRIVATE="1" TAGS="tag1,tag2">GitHub</A>
            <DD>comment for the bookmark here
            second line of the comment here
            third line of the comment here
            <DT><A HREF="https://news.com/" ADD_DATE="1360951967" PRIVATE="1" TAGS="tag1,tag2,tag3">News</A>""",
            (
                (
                    'https://github.com/j', 'GitHub', ',tag1,tag2,',
                    'comment for the bookmark here\n            '
                    'second line of the comment here\n            '
                    'third line of the comment here',
                    0, True, False
                ),
                ('https://news.com/', 'News', ',tag1,tag2,tag3,', None, 0, True, False)
            )
        ),
        (

            """DT><A HREF="https://github.com/j" ADD_DATE="1360951967" PRIVATE="1" TAGS="tag1,tag2">GitHub</A>
            <DD>comment for the bookmark here""",
            ((
                'https://github.com/j', 'GitHub', ',tag1,tag2,',
                'comment for the bookmark here', 0, True, False
            ),)
        )

    ]
)
def test_import_html(html_text, exp_res):
    """test method."""
    from buku import import_html
    from bs4 import BeautifulSoup
    html_soup = BeautifulSoup(html_text, 'html.parser')
    res = list(import_html(html_soup, False, None))
    for item, exp_item in zip(res, exp_res):
        assert item == exp_item, 'Actual item:\n{}'.format(item)


def test_import_html_and_add_parent():
    from buku import import_html
    from bs4 import BeautifulSoup
    html_text = """<DT><H3>1s</H3>
<DL><p>
<DT><A HREF="http://example.com/"></A>"""
    exp_res = ('http://example.com/', None, ',1s,', None, 0, True, False)
    html_soup = BeautifulSoup(html_text, 'html.parser')
    res = list(import_html(html_soup, True, None))
    assert res[0] == exp_res


def test_import_html_and_new_tag():
    from buku import import_html
    from bs4 import BeautifulSoup
    html_text = """<DT><A HREF="https://github.com/j" TAGS="tag1,tag2">GitHub</A>
<DD>comment for the bookmark here"""
    exp_res = (
        'https://github.com/j', 'GitHub', ',tag1,tag2,tag3,',
        'comment for the bookmark here', 0, True, False
    )
    html_soup = BeautifulSoup(html_text, 'html.parser')
    res = list(import_html(html_soup, False, 'tag3'))
    assert res[0] == exp_res


@pytest.mark.parametrize(
    'platform, params',
    [
        ['linux', ['xsel', '-b', '-i']],
        ['freebsd', ['xsel', '-b', '-i']],
        ['openbsd', ['xsel', '-b', '-i']],
        ['darwin', ['pbcopy']],
        ['win32', ['clip']],
        ['random', None],
    ],
)
def test_copy_to_clipboard(platform, params):
    # m_popen = mock.Mock()
    content = mock.Mock()
    m_popen_retval = mock.Mock()
    platform_recognized = \
        platform.startswith(('linux', 'freebsd', 'openbsd')) \
        or platform in ('darwin', 'win32')
    with mock.patch('buku.sys') as m_sys, \
            mock.patch('buku.Popen', return_value=m_popen_retval) as m_popen, \
            mock.patch('buku.shutil.which', return_value=True):
        m_sys.platform = platform
        from buku import copy_to_clipboard
        import subprocess
        copy_to_clipboard(content)
        if platform_recognized:
            m_popen.assert_called_once_with(
                params, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            m_popen_retval.communicate.assert_called_once_with(content)
        else:
            logging.info('popen is called {} on unrecognized platform'.format(m_popen.call_count))


@pytest.mark.parametrize('export_type, exp_res', [
    [
        'html',
        '<!DOCTYPE NETSCAPE-Bookmark-file-1>\n\n'
        '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">\n'
        '<TITLE>Bookmarks</TITLE>\n<H1>Bookmarks</H1>\n\n<DL><p>\n'
        '    <DT><H3 ADD_DATE="1556430615" LAST_MODIFIED="1556430615" PERSONAL_TOOLBAR_FOLDER="true">buku bookmarks</H3>\n'
        '    <DL><p>\n'
        '        <DT><A HREF="htttp://example.com" ADD_DATE="1556430615" LAST_MODIFIED="1556430615"></A>\n'
        '        <DT><A HREF="htttp://example.org" ADD_DATE="1556430615" LAST_MODIFIED="1556430615"></A>\n'
        '        <DT><A HREF="http://google.com" ADD_DATE="1556430615" LAST_MODIFIED="1556430615">Google</A>\n'
        '    </DL><p>\n</DL><p>'
    ],
    ['org', '* [[htttp://example.com][Untitled]]\n* [[htttp://example.org][Untitled]]\n* [[http://google.com][Google]]\n'],
    ['markdown', '- [Untitled](htttp://example.com)\n- [Untitled](htttp://example.org)\n- [Google](http://google.com)\n'],
    ['random', None],
])
def test_convert_bookmark_set(export_type, exp_res, monkeypatch):
    from buku import convert_bookmark_set
    import buku
    bms = [
        (1, 'htttp://example.com', '', ',', '', 0),
        (1, 'htttp://example.org', None, ',', '', 0),
        (2, 'http://google.com', 'Google', ',', '', 0)]
    if export_type == 'random':
        with pytest.raises(AssertionError):
            convert_bookmark_set(bms, export_type=export_type)
    else:

        def return_fixed_number():
            return 1556430615
        monkeypatch.setattr(buku.time, 'time', return_fixed_number)
        res = convert_bookmark_set(bms, export_type=export_type)
        assert res['count'] == 3
        assert exp_res == res['data']


@pytest.mark.parametrize('tags,data', [
    [',', '\n'],
    [',tag1,tag2,', ' :tag1:tag2:\n'],
    [',word1 word2,', ' :word1_word2:\n'],
    [',word1:word2,', ' :word1_word2:\n'],
    [',##tag##,', ' :_tag_:\n'],
    [',##tag##,!!tag!!,', ' :_tag_:\n'],
    [',home / personal,', ' :home_personal:\n'],
])
def test_convert_tags_to_org_mode_tags(tags, data):
    from buku import convert_tags_to_org_mode_tags
    res = convert_tags_to_org_mode_tags(tags)
    assert res == data
