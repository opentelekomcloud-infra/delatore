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
    a = 5
    assert update is not None


async def test_trigger_from_loop_lb_down(influxdb_lb_down: InfluxSourceLBDOWN, pub: Client, sub: Client):
    await sub.subscribe(influxdb_lb_down.TOPIC)
    await asyncio.sleep(.1)
    update = await sub.get(5)
    assert update is not None

@pytest.fixture
async def influxdb_lb_timing_result_1(service):
    src = InfluxSourceLBTiming(service.get_client())
    src.threshold = 0
    src.ignore_duplicates = False
    loop = asyncio.get_running_loop()
    loop.create_task(src.start(asyncio.Event()))
    await asyncio.sleep(.1)
    return src

@pytest.fixture
async def influxdb_lb_timing_result_2(service):
    src = InfluxSourceLBTiming(service.get_client())
    src.threshold = 60
    src.ignore_duplicates = False
    loop = asyncio.get_running_loop()
    loop.create_task(src.start(asyncio.Event()))
    await asyncio.sleep(.1)
    return src

@pytest.fixture
async def influxdb_lb_timing_result_3(service):
    src = InfluxSourceLBTiming(service.get_client())
    src.threshold = 90
    src.ignore_duplicates = False
    loop = asyncio.get_running_loop()
    loop.create_task(src.start(asyncio.Event()))
    await asyncio.sleep(.1)
    return src


@pytest.mark.parametrize(
    "src, check",
    [(influxdb_lb_timing_result_1, 'error'), (influxdb_lb_timing_result_2, 'ok'),(influxdb_lb_timing_result_3, 'ok')],
)
async def test_result_lb_timing(src, check, pub: Client, sub: Client):
    await sub.subscribe(src.TOPIC)
    await asyncio.sleep(.1)
    update = await sub.get(5)
    if check == 'error':
         assert "status_list" in update
    if check == 'ok':
         assert "- LB_LOAD" in update
    assert update is not None
