"""test module."""
from itertools import product
from unittest import mock

import pytest


@pytest.mark.parametrize("platform, file", product(['win32', 'linux'], [None, mock.Mock()]))
def test_program_info(platform, file):
    """test method."""
    with mock.patch('buku.sys') as m_sys:
        import buku
        prog_info_text = '''
SYMBOLS:
      >                    title
      +                    comment
      #                    tags

Version {}
Copyright © 2015-2017 {}
License: {}
Webpage: https://github.com/jarun/Buku
'''.format(buku.__version__, buku.__author__, buku.__license__)
        file = mock.Mock()
        if file is None:
            buku.ExtendedArgumentParser.program_info()
        else:
            buku.ExtendedArgumentParser.program_info(file)
        if platform == 'win32' and file == m_sys.stdout:
            m_sys.stderr.write.assert_called_once_with(prog_info_text)
        else:
            file.write.assert_called_once_with(prog_info_text)


def test_prompt_help():
    """test method."""
    file = mock.Mock()
    import buku
    buku.ExtendedArgumentParser.prompt_help(file)
    file.write.assert_called_once_with('''
keys:
  1-N                    browse search result indices and/or ranges
  a                      open all results in browser
  s keyword [...]        search for records with ANY keyword
  S keyword [...]        search for records with ALL keywords
  d                      match substrings ('pen' matches 'opened')
  r expression           run a regex search
  t [...]                search bookmarks by a tag or show tag list
  g [...][>>|>|<<][...]  append, remove tags to/from indices and/or ranges
  p [...]                print bookmarks by indices and/or ranges
  w [editor|index]       edit and add or update a bookmark
                         (tag list index fetches bookmarks by tag)
  ?                      show this help
  q, ^D, double Enter    exit buku

''')


def test_print_help():
    """test method."""
    file = mock.Mock()
    import buku
    obj = buku.ExtendedArgumentParser()
    obj.program_info = mock.Mock()
    obj.print_help(file)
    obj.program_info.assert_called_once_with(file)
