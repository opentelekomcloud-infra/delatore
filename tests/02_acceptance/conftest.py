import asyncio

import pytest

from delatore.configuration import DEFAULT_INSTANCE_CONFIG
from delatore.sources import (AWXApiSource, InfluxSource, InfluxSourceAutoscaling, InfluxSourceLBDOWN, \
                              InfluxSourceDiskStateRead, InfluxSourceDiskStateWrite, InfluxSourceDiskStateReadSFS,\
                              InfluxSourceDiskStateWriteSFS, InfluxSourceRDSTest, InfluxSourceLBTiming, InfluxSourceLBDOWNFailCount,)


@pytest.fixture
async def influxdb(service):
    src = InfluxSource(service.get_client())
    src.ignore_duplicates = False
    loop = asyncio.get_running_loop()
    loop.create_task(src.start(asyncio.Event()))
    await asyncio.sleep(.1)
    return src


@pytest.fixture
async def influxdb_lb_timing(service):
    src = InfluxSourceLBTiming(service.get_client())
    src.ignore_duplicates = False
    loop = asyncio.get_running_loop()
    loop.create_task(src.start(asyncio.Event()))
    await asyncio.sleep(.1)
    return src


@pytest.fixture
async def influxdb_disk_read(service):
    src = InfluxSourceDiskStateRead(service.get_client())
    src.ignore_duplicates = False
    loop = asyncio.get_running_loop()
    loop.create_task(src.start(asyncio.Event()))
    await asyncio.sleep(.1)
    return src


@pytest.fixture
async def influxdb_disk_write(service):
    src = InfluxSourceDiskStateWrite(service.get_client())
    src.ignore_duplicates = False
    loop = asyncio.get_running_loop()
    loop.create_task(src.start(asyncio.Event()))
    await asyncio.sleep(.1)
    return src


@pytest.fixture
async def influxdb_disk_read_sfs(service):
    src = InfluxSourceDiskStateReadSFS(service.get_client())
    src.ignore_duplicates = False
    loop = asyncio.get_running_loop()
    loop.create_task(src.start(asyncio.Event()))
    await asyncio.sleep(.1)
    return src


@pytest.fixture
async def influxdb_disk_write_sfs(service):
    src = InfluxSourceDiskStateWriteSFS(service.get_client())
    src.ignore_duplicates = False
    loop = asyncio.get_running_loop()
    loop.create_task(src.start(asyncio.Event()))
    await asyncio.sleep(.1)
    return src


@pytest.fixture
async def influxdb_lb_down_fail_count(service):
    src = InfluxSourceLBDOWNFailCount(service.get_client())
    src.ignore_duplicates = False
    loop = asyncio.get_running_loop()
    loop.create_task(src.start(asyncio.Event()))
    await asyncio.sleep(.1)
    return src


@pytest.fixture
async def influxdb_lb_down(service):
    src = InfluxSourceLBDOWN(service.get_client())
    src.ignore_duplicates = False
    loop = asyncio.get_running_loop()
    loop.create_task(src.start(asyncio.Event()))
    await asyncio.sleep(.1)
    return src


@pytest.fixture
async def awx_client(service):
    src = AWXApiSource(service.get_client(), DEFAULT_INSTANCE_CONFIG)
    src.ignore_duplicates = False
    stop_ev = asyncio.Event()
    asyncio.create_task(src.start(stop_ev))
    await asyncio.sleep(.1)
    yield src
    stop_ev.set()


@pytest.fixture
async def influxdb_lb_timing_result_error(service):
    src = InfluxSourceLBTiming(service.get_client())
    src.threshold = -1
    src.ignore_duplicates = False
    loop = asyncio.get_running_loop()
    loop.create_task(src.start(asyncio.Event()))
    await asyncio.sleep(.1)
    return src


@pytest.fixture
async def influxdb_lb_timing_result_ok(service):
    src = InfluxSourceLBTiming(service.get_client())
    src.threshold = 500
    src.ignore_duplicates = False
    loop = asyncio.get_running_loop()
    loop.create_task(src.start(asyncio.Event()))
    await asyncio.sleep(.1)
    return src


@pytest.fixture
async def influxdb_lb_down_fail_count_error(service):
    src = InfluxSourceLBDOWNFailCount(service.get_client())
    src.threshold = -1
    src.ignore_duplicates = False
    loop = asyncio.get_running_loop()
    loop.create_task(src.start(asyncio.Event()))
    await asyncio.sleep(.1)
    return src


@pytest.fixture
async def influxdb_lb_down_fail_count_ok(service):
    src = InfluxSourceLBDOWNFailCount(service.get_client())
    src.threshold = 10
    src.ignore_duplicates = False
    loop = asyncio.get_running_loop()
    loop.create_task(src.start(asyncio.Event()))
    await asyncio.sleep(.1)
    return src


@pytest.fixture
async def influxdb_autoscaling(service):
    src = InfluxSourceAutoscaling(service.get_client())
    src.threshold = 10
    src.ignore_duplicates = False
    loop = asyncio.get_running_loop()
    loop.create_task(src.start(asyncio.Event()))
    await asyncio.sleep(.1)
    return src


@pytest.fixture
async def influxdb_rds_test(service):
    src = InfluxSourceRDSTest(service.get_client())
    src.threshold = 10
    src.ignore_duplicates = False
    loop = asyncio.get_running_loop()
    loop.create_task(src.start(asyncio.Event()))
    await asyncio.sleep(.1)
    return src
