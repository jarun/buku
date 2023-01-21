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


def test_bukuserver_requirement(setup_obj):
    assert [
        x
        for x in pathlib.Path("bukuserver/requirements.txt").read_text(encoding="utf8", errors="surrogateescape").splitlines()
        if "flask-reverse-proxy-fix" not in x
    ] == setup_obj.server_require


def test_buku_requirement(setup_obj):
    assert sorted(
        [
            x
            for x in pathlib.Path("requirements.txt").read_text(encoding="utf8", errors="surrogateescape").splitlines()
            if not x.startswith('#') and x != 'setuptools'
        ]
    ) == sorted(setup_obj.install_requires)
