import asyncio

import pytest

from delatore.sources import AWXWebHookSource


@pytest.fixture
async def awx_web_hook_src(service):
    src = AWXWebHookSource(service.get_client())
    src.polling_interval = .1
    src.request_timeout = .1
    stop_ev = asyncio.Event()
    src_task = asyncio.create_task(src.start(stop_ev))
    await asyncio.sleep(.1)
    await asyncio.wait_for(asyncio.open_connection('localhost', src.port), 5)
    yield src
    stop_ev.set()
    await src.stop()
    await src_task
