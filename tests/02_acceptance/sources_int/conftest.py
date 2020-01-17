import pytest

from delatore.sources import AWXApiClient


@pytest.fixture(scope='session')
def awx_client(service):
    return AWXApiClient(service.get_client())
