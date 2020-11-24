"""test module."""
from unittest import mock
import os
import random

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


@pytest.mark.parametrize(
    'filesize',
    list(range(0, 17)) + [511, 512, 513, 1023, 1024, 1025, 524288, 524289, 1000000, 1048576, 2097152, 4194304]
)
def test_encrypt_decrypt(tmpdir, filesize):
    """test method."""
    dbfile = os.path.join(tmpdir.strpath, 'test_encrypt_decrypt_dbfile')
    content = bytes(random.getrandbits(8) for _ in range(filesize))
    with open(dbfile, 'wb') as fp:
        fp.write(content)
    assert os.stat(dbfile).st_size == filesize
    with mock.patch('getpass.getpass', return_value='password'):
        from buku import BukuCrypt
        with pytest.raises(SystemExit):
            BukuCrypt.encrypt_file(1, dbfile=dbfile)
        BukuCrypt.decrypt_file(1, dbfile=dbfile)
    assert os.path.exists(dbfile)
    with open(dbfile, 'rb') as fp:
        roundtrip_content = fp.read()
    assert roundtrip_content == content
