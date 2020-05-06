import asyncio

import pytest

from delatore.configuration import DEFAULT_INSTANCE_CONFIG
from delatore.sources import AWXApiSource, InfluxSource, InfluxSourceLBTiming, InfluxSourceLBDOWN, InfluxSourceLBDOWNFailCount


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
async def influxdb_lb_timing_result_error(service_function1):
    src = InfluxSourceLBTiming(service_function1.get_client())
    src.threshold = -1
    src.ignore_duplicates = False
    loop = asyncio.get_running_loop()
    loop.create_task(src.start(asyncio.Event()))
    await asyncio.sleep(.1)
    return src


@pytest.fixture
async def influxdb_lb_timing_result_ok(service_function2):
    src = InfluxSourceLBTiming(service_function2.get_client())
    src.threshold = 500
    src.ignore_duplicates = False
    loop = asyncio.get_running_loop()
    loop.create_task(src.start(asyncio.Event()))
    await asyncio.sleep(.1)
    return src


@pytest.fixture
async def influxdb_lb_down_fail_count_error(service_function1):
    src = InfluxSourceLBDOWNFailCount(service_function1.get_client())
    src.threshold = -1
    src.ignore_duplicates = False
    loop = asyncio.get_running_loop()
    loop.create_task(src.start(asyncio.Event()))
    await asyncio.sleep(.1)
    return src


@pytest.fixture
async def influxdb_lb_down_fail_count_ok(service_function2):
    src = InfluxSourceLBDOWNFailCount(service_function2.get_client())
    src.threshold = 10
    src.ignore_duplicates = False
    loop = asyncio.get_running_loop()
    loop.create_task(src.start(asyncio.Event()))
    await asyncio.sleep(.1)
    return src