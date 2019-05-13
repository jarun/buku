def test_bukuserver_requirement(monkeypatch):
    def m_setup(**kwargs):
        return None
    import setuptools
    monkeypatch.setattr(setuptools, 'setup', m_setup)
    import setup
    setup_l = setup.server_require
    with open('bukuserver/requirements.txt') as f:
        bs_l = [x for x in f.read().splitlines() if not x.startswith('buku')]
    assert bs_l == setup_l
