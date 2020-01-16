import asyncio

import pytest


@pytest.fixture
async def sub(service):
    _sub = service.get_client()
    await _sub.start_consuming()
    await asyncio.sleep(.01)
    return _sub


@pytest.fixture
def pub(service):
    return service.get_client()
