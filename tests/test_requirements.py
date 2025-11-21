import pathlib
import sys
from typing import Any

import pytest

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

ROOT_DIR = pathlib.Path(__file__).parents[1]


@pytest.fixture(scope='module')
def pyproject() -> dict[str, Any]:
    data = (ROOT_DIR / 'pyproject.toml').read_text()
    return tomllib.loads(data)['project']


_reqs = lambda path: [s for s in pathlib.Path(path).read_text(encoding='utf8', errors='surrogateescape').splitlines()
                      if not s.startswith('#') and s != 'setuptools']


def test_bukuserver_requirement(pyproject: dict[str, Any]):
    assert sorted(_reqs('bukuserver/requirements.txt')) == sorted(pyproject['optional-dependencies']['server'])


def test_buku_requirement(pyproject: dict[str, Any]):
    assert sorted(_reqs('requirements.txt')) == sorted(pyproject['dependencies'])
