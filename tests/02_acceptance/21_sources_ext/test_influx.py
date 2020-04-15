import asyncio

import pytest
from apubsub.client import Client

from delatore.sources import InfluxSource, InfluxSourceLBTiming
pytestmark = pytest.mark.asyncio


async def test_influx_data(influxdb: InfluxSource):
    update = await influxdb.get_update()
    a = 5
    assert update is not None

async def test_influx_data_lb_timing(influxdb_lb_timing: InfluxSourceLBTiming):
    update = await influxdb_lb_timing.get_update()
    assert update is not None


async def test_trigger_from_loop(influxdb: InfluxSource, pub: Client, sub: Client):
    await sub.subscribe(influxdb.TOPIC)
    await asyncio.sleep(.1)
    update = await sub.get(5)
    assert update is not None


async def test_trigger_from_loop_lb_down(influxdb: InfluxSource, pub: Client, sub: Client):
    await sub.subscribe(influxdb.TOPIC)
    await asyncio.sleep(.1)
    update = await sub.get(5)
    assert update is not None

