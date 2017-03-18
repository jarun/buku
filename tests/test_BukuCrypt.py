"""test module."""
from unittest import mock
import os

import pytest


def test_get_filehash(tmpdir):
    """test method."""
    exp_res = b'\x9f\x86\xd0\x81\x88L}e\x9a/\xea\xa0\xc5Z\xd0\x15\xa3\xbfO\x1b+\x0b\x82,\xd1]l\x15\xb0\xf0\n\x08'  # NOQA
    test_file = os.path.join(tmpdir.strpath, 'my_test_file.txt')
    with open(test_file, 'w') as f:
        f.write('test')
    from buku import BukuCrypt
    res = BukuCrypt.get_filehash(test_file)
    assert res == exp_res


def touch(fname):
    """touch implementation for python."""
    if os.path.exists(fname):
        os.utime(fname, None)
    else:
        open(fname, 'a').close()


def test_encrypt_decrypt(tmpdir):
    """test method."""
    dbfile = os.path.join(tmpdir.strpath, 'test_encrypt_decrypt_dbfile')
    touch(dbfile)
    with mock.patch('getpass.getpass', return_value='password'):
        from buku import BukuCrypt
        with pytest.raises(SystemExit):
            BukuCrypt.encrypt_file(1, dbfile=dbfile)
        BukuCrypt.decrypt_file(1, dbfile=dbfile)
