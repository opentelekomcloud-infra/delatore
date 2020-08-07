import asyncio

import pytest
from apubsub.client import Client

from delatore.sources import (InfluxSource,  InfluxSourceAutoscaling, InfluxSourceDiskStateRead, InfluxSourceDiskStateReadSFS,
                              InfluxSourceDiskStateWrite, InfluxSourceDiskStateWriteSFS, InfluxSourceLBDOWN, InfluxSourceRDSTest,
                              InfluxSourceLBDOWNFailCount, InfluxSourceLBTiming)
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


async def test_influx_data_disk_read(influxdb_disk_read: InfluxSourceDiskStateRead):
    update = await influxdb_disk_read.get_update()
    assert update is not None


async def test_influx_data_disk_write(influxdb_disk_write: InfluxSourceDiskStateWrite):
    update = await influxdb_disk_write.get_update()
    assert update is not None


async def test_influx_data_disk_read_sfs(influxdb_disk_read_sfs: InfluxSourceDiskStateReadSFS):
    update = await influxdb_disk_read_sfs.get_update()
    assert update is not None


async def test_influx_data_disk_write_sfs(influxdb_disk_write_sfs: InfluxSourceDiskStateWriteSFS):
    update = await influxdb_disk_write_sfs.get_update()
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


async def test_result_lb_timing_error(influxdb_lb_timing_result_error: InfluxSourceLBTiming, sub):
    await sub.subscribe(influxdb_lb_timing_result_error.TOPICS.changes)
    await asyncio.sleep(.1)
    update = await sub.get(15)
    if '"status": "fail"' not in update:
        assert 'Alert message' in update



async def test_result_lb_timing_ok(influxdb_lb_timing_result_ok: InfluxSourceLBTiming, sub):
    await sub.subscribe(influxdb_lb_timing_result_ok.TOPICS.changes)
    await asyncio.sleep(.1)
    update = await sub.get(15)
    assert 'Alert message' not in update


@pytest.mark.skip
async def test_result_lb_down_fail_count_error(influxdb_lb_down_fail_count_error: InfluxSourceLBDOWNFailCount, sub):
    await sub.subscribe(influxdb_lb_down_fail_count_error.TOPICS.changes)
    await asyncio.sleep(.1)
    update = await sub.get(15)
    if '"status": "fail"' not in update:
        assert 'Alert message' in update


@pytest.mark.skip
async def test_result_lb_down_fail_count_ok(influxdb_lb_down_fail_count_ok: InfluxSourceLBDOWNFailCount, sub):
    await sub.subscribe(influxdb_lb_down_fail_count_ok.TOPICS.changes)
    await asyncio.sleep(.1)
    update = await sub.get(5)
    assert 'Alert message' not in update


async def test_influx_autoscaling(influxdb_autoscaling: InfluxSourceAutoscaling):
    update = await influxdb_autoscaling.get_update()
    assert update is not None


async def test_trigger_autoscaling(influxdb_autoscaling: InfluxSourceAutoscaling, sub: Client):
    await sub.subscribe(influxdb_autoscaling.TOPICS.changes)
    await asyncio.sleep(.1)
    update = await sub.get(5)
    assert update is not None


async def test_influx_rds_test(influxdb_rds_test: InfluxSourceRDSTest):
    update = await influxdb_rds_test.get_update()
    assert update is not None


async def test_trigger_rds_test(influxdb_rds_test: InfluxSourceRDSTest, sub: Client):
    await sub.subscribe(influxdb_rds_test.TOPICS.changes)
    await asyncio.sleep(.1)
    update = await sub.get(5)
    assert update is not None
