import pytest
from apubsub.client import Client

from delatore.sources import (InfluxSource, InfluxSourceAutoscaling, InfluxSourceDiskStateRead,
                              InfluxSourceDiskStateReadSFS, InfluxSourceDiskStateWrite, InfluxSourceDiskStateWriteSFS,
                              InfluxSourceLBDOWN, InfluxSourceLBDOWNFailCount, InfluxSourceLBTiming,
                              InfluxSourceRDSTest)

pytestmark = pytest.mark.asyncio


async def test_influx_data(influxdb: InfluxSource):
    update = await influxdb.get_update()
    assert update is not None


async def test_trigger_from_loop(influxdb: InfluxSource, sub: Client):
    await sub.subscribe(influxdb.TOPICS.changes)
    update = await sub.get(5)
    assert update is not None


async def test_influx_data_lb_timing(influxdb_lb_timing: InfluxSourceLBTiming):
    update = await influxdb_lb_timing.get_update()
    assert update is not None


async def test_trigger_from_loop_lb_timing(influxdb_lb_timing: InfluxSourceLBTiming, sub: Client):
    await sub.subscribe(influxdb_lb_timing.TOPICS.error)
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


async def test_influx_data_lb_down_fail_count(influxdb_lb_down_fail_count: InfluxSourceLBDOWNFailCount):
    update = await influxdb_lb_down_fail_count.get_update()
    assert update is not None


async def test_trigger_from_loop_lb_down(influxdb_lb_down: InfluxSourceLBDOWN, sub: Client):
    await sub.subscribe(influxdb_lb_down.TOPICS.error)
    update = await sub.get(5)
    assert update is not None


async def test_result_lb_timing_error(influxdb_lb_timing_result_error: InfluxSourceLBTiming, sub: Client):
    await sub.subscribe(influxdb_lb_timing_result_error.TOPICS.error)
    update = await sub.get(5)
    assert update is not None


async def test_result_lb_down_fail_count_error(influxdb_lb_down_fail_count_error: InfluxSourceLBDOWNFailCount,
                                               sub: Client):
    await sub.subscribe(influxdb_lb_down_fail_count_error.TOPICS.error)
    update = await sub.get(5)
    assert update is not None


async def test_influx_autoscaling(influxdb_autoscaling: InfluxSourceAutoscaling):
    update = await influxdb_autoscaling.get_update()
    assert update is not None


async def test_trigger_autoscaling(influxdb_autoscaling: InfluxSourceAutoscaling, sub: Client):
    await sub.subscribe(influxdb_autoscaling.TOPICS.error)
    update = await sub.get(5)
    assert update is not None


async def test_influx_rds_test(influxdb_rds_test: InfluxSourceRDSTest):
    update = await influxdb_rds_test.get_update()
    assert update is not None


async def test_trigger_rds_test(influxdb_rds_test: InfluxSourceRDSTest, sub: Client):
    await sub.subscribe(influxdb_rds_test.TOPICS.error)
    update = await sub.get(5)
    assert update is not None
