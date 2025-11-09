import pathlib

import pytest


@pytest.fixture
def setup_obj(monkeypatch):
    def m_setup(**_):
        return None
    import setuptools
    monkeypatch.setattr(setuptools, 'setup', m_setup)
    import setup

    return setup

_reqs = lambda path: [s for s in pathlib.Path(path).read_text(encoding='utf8', errors='surrogateescape').splitlines()
                      if not s.startswith('#') and s != 'setuptools']


def test_bukuserver_requirement(setup_obj):
    assert sorted(_reqs('bukuserver/requirements.txt')) == sorted(setup_obj.server_require)

def test_buku_requirement(setup_obj):
    assert sorted(_reqs('requirements.txt')) == sorted(setup_obj.install_requires)
