import asyncio

import pytest
from apubsub import Service


@pytest.fixture(scope='session')
def service():
    service = Service()
    service.start()
    yield service
    service.stop()


@pytest.fixture(scope='session')
def stop_event():
    return asyncio.Event()


@pytest.fixture
def event_loop():
    return asyncio.get_event_loop()
