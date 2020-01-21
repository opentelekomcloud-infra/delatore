import asyncio

import pytest
from apubsub.client import Client

pytestmark = pytest.mark.asyncio


async def test_influx_data(influxdb):
    update = await influxdb.get_update()
    assert update is not None


async def test_trigger_from_loop(influxdb, pub: Client, sub: Client):
    await sub.subscribe(influxdb.TOPIC)
    await asyncio.sleep(.1)
    update = await sub.get(5)
    assert update is not None
