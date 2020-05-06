import asyncio

import pytest
from apubsub.client import Client

from delatore.sources import InfluxSource, InfluxSourceLBTiming, InfluxSourceLBDOWN, InfluxSourceLBDOWNFailCount
pytestmark = pytest.mark.asyncio


async def test_influx_data(influxdb: InfluxSource):
    update = await influxdb.get_update()
    assert update is not None


async def test_trigger_from_loop(influxdb: InfluxSource, sub: Client):
    await sub.subscribe(influxdb.TOPICS.changes)
    await asyncio.sleep(.1)
    update = await sub.get(5)
    assert update is not None


async def test_influx_data_lb_timing(influxdb_lb_timing: InfluxSourceLBTiming):
    update = await influxdb_lb_timing.get_update()
    assert update is not None


async def test_trigger_from_loop_lb_timing(influxdb_lb_timing: InfluxSourceLBTiming, sub: Client):
    await sub.subscribe(influxdb_lb_timing.TOPICS.changes)
    await asyncio.sleep(.1)
    update = await sub.get(5)
    assert update is not None


async def test_influx_data_lb_down(influxdb_lb_down: InfluxSourceLBDOWN):
    update = await influxdb_lb_down.get_update()
    assert update is not None


async def test_trigger_from_loop_lb_down_fail_count(influxdb_lb_down: InfluxSourceLBDOWN, sub: Client):
    await sub.subscribe(influxdb_lb_down.TOPICS.changes)
    await asyncio.sleep(.1)
    update = await sub.get(5)
    assert update is not None


async def test_influx_data_lb_down_fail_count(influxdb_lb_down_fail_count: InfluxSourceLBDOWNFailCount):
    update = await influxdb_lb_down_fail_count.get_update()
    assert update is not None


async def test_trigger_from_loop_lb_down(influxdb_lb_down: InfluxSourceLBDOWN, sub: Client):
    await sub.subscribe(influxdb_lb_down.TOPICS.changes)
    await asyncio.sleep(.1)
    update = await sub.get(5)
    assert update is not None

