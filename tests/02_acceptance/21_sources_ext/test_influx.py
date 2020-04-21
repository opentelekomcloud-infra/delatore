import asyncio

import pytest
from apubsub.client import Client

from delatore.sources import InfluxSource, InfluxSourceLBTiming, InfluxSourceLBDOWN
pytestmark = pytest.mark.asyncio


async def test_influx_data(influxdb: InfluxSource):
    update = await influxdb.get_update()
    assert update is not None


async def test_trigger_from_loop(influxdb: InfluxSource, pub: Client, sub: Client):
    await sub.subscribe(influxdb.TOPICS.changes)
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
    await sub.subscribe(influxdb_lb_timing.TOPICS.changes)
    await asyncio.sleep(.1)
    update = await sub.get(5)
    assert update is not None


async def test_trigger_from_loop_lb_down(influxdb_lb_down: InfluxSourceLBDOWN, pub: Client, sub: Client):
    await sub.subscribe(influxdb_lb_down.TOPICS.changes)
    await asyncio.sleep(.1)
    update = await sub.get(5)
    assert update is not None


async def test_result_lb_timing_error(influxdb_lb_timing_result_error: InfluxSourceLBTiming, pub, sub):
    await sub.subscribe(influxdb_lb_timing_result_error.TOPICS.changes)
    await asyncio.sleep(.1)
    update = await sub.get(5)
    assert "- LB_LOAD" in update

async def test_result_lb_timing_ok1(influxdb_lb_timing_result_ok1: InfluxSourceLBTiming, pub, sub):
    await sub.subscribe(influxdb_lb_timing_result_ok1.TOPICS.changes)
    await asyncio.sleep(.1)
    update = await sub.get(5)
    assert "status_list" in update

async def test_result_lb_timing_ok2(influxdb_lb_timing_result_ok2: InfluxSourceLBTiming, pub, sub):
    await sub.subscribe(influxdb_lb_timing_result_ok2.TOPICS.changes)
    await asyncio.sleep(.1)
    update = await sub.get(5)
    assert "status_list" in update

