import pytest

from delatore.sources import InfluxSource


@pytest.fixture(scope='session')
def influxdb(service):
    return InfluxSource(service.get_client())
