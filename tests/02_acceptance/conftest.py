import pytest

from delatore.sources import AWXApiClient, InfluxSource


@pytest.fixture(scope='session')
def awx_client():
    return AWXApiClient()


@pytest.fixture(scope='session')
def influxdb():
    return InfluxSource()
