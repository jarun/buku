import pathlib


def test_bukuserver_requirement(monkeypatch):
    def m_setup(**kwargs):
        return None
    import setuptools
    monkeypatch.setattr(setuptools, 'setup', m_setup)
    import setup

    assert [
        x
        for x in pathlib.Path("bukuserver/requirements.txt").read_text(encoding="utf8", errors="surrogateescape").splitlines()
        if "flask-reverse-proxy-fix" not in x
    ] == setup.server_require
