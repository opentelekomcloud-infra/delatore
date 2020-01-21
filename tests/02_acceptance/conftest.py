import asyncio

import pytest

from delatore.sources import InfluxSource


@pytest.fixture
async def influxdb(service):
    src = InfluxSource(service.get_client())
    src.ignore_duplicates = False
    loop = asyncio.get_running_loop()
    loop.create_task(src.start(asyncio.Event()))
    return src
