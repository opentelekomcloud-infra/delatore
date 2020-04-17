import asyncio

import pytest
from apubsub.client import Client

from delatore.sources import InfluxSource

pytestmark = pytest.mark.asyncio


async def test_influx_data(influxdb: InfluxSource):
    update = await influxdb.get_update()
    assert update is not None


async def test_trigger_from_loop(influxdb: InfluxSource, pub: Client, sub: Client):
    await sub.subscribe(influxdb.TOPICS.changes)
    await asyncio.sleep(.1)
    update = await sub.get(5)
    assert update is not None
