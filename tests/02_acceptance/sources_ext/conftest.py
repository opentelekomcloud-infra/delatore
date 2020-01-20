import asyncio

import pytest

from delatore.sources import AWXApiSource


@pytest.fixture
async def awx_client(service):
    src = AWXApiSource(service.get_client())
    stop_ev = asyncio.Event()
    asyncio.create_task(src.start(stop_ev, False))
    yield src
    stop_ev.set()
