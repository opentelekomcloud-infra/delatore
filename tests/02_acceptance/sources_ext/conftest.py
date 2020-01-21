import asyncio

import pytest

from delatore.sources import AWXApiSource, AWXWebHookSource


@pytest.fixture
async def awx_client(service):
    src = AWXApiSource(service.get_client())
    stop_ev = asyncio.Event()
    asyncio.create_task(src.start(stop_ev))
    yield src
    stop_ev.set()


@pytest.fixture
async def awx_web_hook_src(service):
    src = AWXWebHookSource(service.get_client())
    stop_ev = asyncio.Event()
    asyncio.create_task(src.start(stop_ev))
    await asyncio.sleep(.05)
    await asyncio.wait_for(asyncio.open_connection('localhost', src.port), 5)
    yield src
    stop_ev.set()
    await src.stop()
