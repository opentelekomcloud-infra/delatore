import asyncio

import pytest

from delatore.sources import start_sources


@pytest.mark.asyncio
async def test_sources_start(service):
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    task = loop.create_task(start_sources(service, stop_event))
    await asyncio.sleep(.5)
    task.cancel()
