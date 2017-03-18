"""test module."""
from itertools import product
from unittest import mock

import pytest


def test_init():
    """test method."""
    from buku import BukuHTMLParser
    obj = BukuHTMLParser()
    assert not obj.in_title_tag
    assert not obj.data
    assert obj.prev_tag is None
    assert obj.parsed_title is None


@pytest.mark.parametrize('tag', ['', 'title'])
def test_handle_starttag(tag):
    """test method."""
    attrs = mock.Mock()
    from buku import BukuHTMLParser
    obj = BukuHTMLParser()
    obj.handle_starttag(tag, attrs)
    if tag == 'title':
        assert obj.in_title_tag
        assert obj.prev_tag == tag
    else:
        assert not obj.in_title_tag


@pytest.mark.parametrize('tag, data', product(['', 'title'], [None, 'data']))
def test_handle_endtag(tag, data):
    """test method."""
    from buku import BukuHTMLParser
    obj = BukuHTMLParser()
    obj.data = data
    obj.reset = mock.Mock()
    obj.handle_endtag(tag)
    # test
    if tag == 'title':
        assert not obj.in_title_tag
    if tag == 'title' and data != '':
        assert obj.parsed_title == data
        obj.reset.assert_called_once_with()


@pytest.mark.parametrize('prev_tag, in_title_tag', product(['', 'title'], [None, 'data']))
def test_handle_data(prev_tag, in_title_tag):
    """test method."""
    new_data = 'new_data'
    from buku import BukuHTMLParser
    obj = BukuHTMLParser()
    obj.prev_tag = prev_tag
    obj.data = ''
    obj.in_title_tag = in_title_tag
    obj.handle_data(new_data)
    if obj.prev_tag == 'title' and in_title_tag:
        assert obj.data == new_data


def test_error():
    """test method."""
    from buku import BukuHTMLParser
    obj = BukuHTMLParser()
    obj.error(message=mock.Mock())
