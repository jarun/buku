import os

import pytest
from vcr import VCR


def pytest_addoption(parser):
    parser.addoption('--record-mode', dest='record_mode', default='none')


@pytest.yield_fixture()
def vcr(request):
    record_mode = request.config.getoption('record_mode')

    vcr = VCR(record_mode=record_mode)

    # Filter the test name so paths aren't interpreted into directories when
    # the files are written
    test_name = os.path.join('vcr_cassettes', request.node.name.replace('/', ''))

    cassette_name = '{}.yaml'.format(os.path.join(os.path.dirname(__file__), test_name))

    with vcr.use_cassette(cassette_name):
        yield
