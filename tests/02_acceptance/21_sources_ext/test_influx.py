import asyncio

import pytest
from apubsub.client import Client

from delatore.sources import InfluxSource, InfluxSourceLBTiming, InfluxSourceLBDOWN
pytestmark = pytest.mark.asyncio


async def test_influx_data(influxdb: InfluxSource):
    update = await influxdb.get_update()
    assert update is not None


async def test_trigger_from_loop(influxdb: InfluxSource, pub: Client, sub: Client):
    await sub.subscribe(influxdb.TOPIC)
    await asyncio.sleep(.1)
    update = await sub.get(5)
    assert update is not None


async def test_influx_data_lb_timing(influxdb_lb_timing: InfluxSourceLBTiming):
    update = await influxdb_lb_timing.get_update()
    assert update is not None


async def test_influx_data_lb_down(influxdb_lb_down: InfluxSourceLBDOWN):
    update = await influxdb_lb_down.get_update()
    assert update is not None


async def test_trigger_from_loop_lb_timing(influxdb_lb_timing: InfluxSourceLBTiming, pub: Client, sub: Client):
    await sub.subscribe(influxdb_lb_timing.TOPIC)
    await asyncio.sleep(.1)
    update = await sub.get(5)
    assert update is not None


async def test_trigger_from_loop_lb_down(influxdb_lb_down: InfluxSourceLBDOWN, pub: Client, sub: Client):
    await sub.subscribe(influxdb_lb_down.TOPIC)
    await asyncio.sleep(.1)
    update = await sub.get(5)
    assert update is not None




