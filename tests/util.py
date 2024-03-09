from unittest import mock
from urllib3 import HTTPResponse
from buku import FetchResult


def mock_http(body=None, **kwargs):
    body = (None if not body else str(body).encode('UTF-8'))
    return mock.patch('urllib3.PoolManager.request', return_value=HTTPResponse(body, **kwargs))

def mock_fetch(custom=None, **kwargs):
    _url = kwargs.pop('url', None)
    status = kwargs.pop('fetch_status', (None if kwargs.get('bad') else 200))
    fn = lambda url, http_head=False: FetchResult(_url or url, fetch_status=status, **kwargs)
    return mock.patch('buku.fetch_data', side_effect=custom or fn)

def _add_rec(db, *args, **kw):
    """Use THIS instead of db.add_rec() UNLESS you want to wait for unnecessary network requests."""
    return db.add_rec(*args, fetch=False, **kw)

def _tagset(s):
    return set(x for x in str(s or '').lower().split(',') if x)
