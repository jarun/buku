"""test module."""
from itertools import product
from unittest import mock

import pytest


@pytest.mark.parametrize("platform, file", product(['win32', 'linux'], [None, mock.Mock()]))
def test_program_info(platform, file):
    """test method."""
    with mock.patch('buku.sys') as m_sys:
        import buku
        file = mock.Mock()
        if file is None:
            buku.ExtendedArgumentParser.program_info()
        else:
            buku.ExtendedArgumentParser.program_info(file)
        if platform == 'win32' and file == m_sys.stdout:
            assert len(m_sys.stderr.write.mock_calls) == 1
        else:
            assert len(file.write.mock_calls) == 1


def test_prompt_help():
    """test method."""
    file = mock.Mock()
    import buku
    buku.ExtendedArgumentParser.prompt_help(file)
    assert len(file.write.mock_calls) == 1


def test_print_help():
    """test method."""
    file = mock.Mock()
    import buku
    obj = buku.ExtendedArgumentParser()
    obj.program_info = mock.Mock()
    obj.print_help(file)
    obj.program_info.assert_called_once_with(file)
