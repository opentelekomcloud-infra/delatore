import asyncio

import pytest

from delatore.sources import AWXApiSource, InfluxSource


@pytest.fixture
async def influxdb(service):
    src = InfluxSource(service.get_client())
    src.ignore_duplicates = False
    loop = asyncio.get_running_loop()
    loop.create_task(src.start(asyncio.Event()))
    return src


@pytest.fixture
async def awx_client(service):
    src = AWXApiSource(service.get_client())
    stop_ev = asyncio.Event()
    asyncio.create_task(src.start(stop_ev))
    yield src
    stop_ev.set()
