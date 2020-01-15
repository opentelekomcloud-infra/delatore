import asyncio

import pytest

from delatore.sources import AWXApiClient, InfluxSource


@pytest.fixture(scope='session')
def awx_client():
    return AWXApiClient(None)


@pytest.fixture(scope='session')
def influxdb():
    return InfluxSource(None)


@pytest.fixture(scope='session')  # change default loop fixture
def event_loop():
    loop = asyncio.get_event_loop()
    return loop
