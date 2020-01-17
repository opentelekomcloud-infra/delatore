import asyncio
import os
import socket

import pytest
from apubsub import Service


@pytest.fixture(scope='session')
def service():
    _service = Service()
    _service.start()

    _socket = socket.socket()
    _socket.settimeout(5)
    try:
        _socket.connect(('localhost', _service.port))
    finally:
        _socket.close()

    yield _service
    _service.stop()


@pytest.fixture
def stop_event():
    return asyncio.Event()


@pytest.fixture(scope='session')
def event_loop():
    return asyncio.get_event_loop()


@pytest.fixture
async def sub(service):
    _sub = service.get_client()
    await _sub.start_consuming()
    await asyncio.sleep(.01)
    return _sub


@pytest.fixture
def pub(service):
    return service.get_client()


@pytest.fixture(scope='session')
def tmp_dir():
    base_path = './tmp'
    os.makedirs(base_path, exist_ok=True)
    yield base_path
    os.rmdir(base_path)
