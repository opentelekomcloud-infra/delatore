import pytest

from delatore.sources import AWXApiSource


@pytest.fixture(scope='session')
def awx_client(service):
    return AWXApiSource(service.get_client())
