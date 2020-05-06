import asyncio

import pytest


from delatore.sources import InfluxSourceLBTiming, InfluxSourceLBDOWNFailCount
pytestmark = pytest.mark.asyncio


async def test_result_lb_timing_error(influxdb_lb_timing_result_error: InfluxSourceLBTiming, sub1):
    await sub1.subscribe(influxdb_lb_timing_result_error.TOPICS.changes)
    await asyncio.sleep(.1)
    update = await sub1.get(15)
    if '"status": "fail"' not in update:
        assert "Alert message" in update


async def test_result_lb_timing_ok(influxdb_lb_timing_result_ok: InfluxSourceLBTiming, sub2):
    await sub2.subscribe(influxdb_lb_timing_result_ok.TOPICS.changes)
    await asyncio.sleep(.1)
    update = await sub2.get(15)
    assert "Alert message" not in update


async def test_result_lb_down_fail_count_error(influxdb_lb_down_fail_count_error: InfluxSourceLBDOWNFailCount, sub1):
    await sub1.subscribe(influxdb_lb_down_fail_count_error.TOPICS.changes)
    await asyncio.sleep(.1)
    update = await sub1.get(15)
    if '"status": "fail"' not in update:
     assert 'Alert message' in update


async def test_result_lb_down_fail_count_ok(influxdb_lb_down_fail_count_ok: InfluxSourceLBDOWNFailCount, sub2):
    await sub2.subscribe(influxdb_lb_down_fail_count_ok.TOPICS.changes)
    await asyncio.sleep(.1)
    update = await sub2.get(5)
    assert 'Alert message' not in update