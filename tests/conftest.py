import asyncio
import os
from asyncio.queues import Queue
from random import choice, randrange

import pytest
from apubsub import Service

from delatore.outputs import BotRunner
from delatore.sources import AWXApiSource, AWXWebHookSource, InfluxSource

from tests.helpers import current_timestamp, random_string, random_with_length


@pytest.fixture(scope='module')
def service():
    _service = Service()
    _service.start()
    yield _service
    _service.stop()


@pytest.fixture
def stop_event():
    return asyncio.Event()


@pytest.fixture
async def sub(service):
    _sub = service.get_client()
    await _sub.start_consuming()
    await asyncio.sleep(.01)
    return _sub


@pytest.fixture
def pub(service):
    return service.get_client()


@pytest.fixture(scope='session')
def tmp_dir():
    base_path = './tmp'
    os.makedirs(base_path, exist_ok=True)
    yield base_path
    os.rmdir(base_path)


@pytest.fixture
def influx_source_data():
    data = [
        {
            'name': 'TEST1_INFLUX',
            'status': 'OK',
            'last_timestamp': '12345678.123',
            'details': None
        },
        {
            'name': 'TEST2_INFLUX',
            'status': 'FAIL',
            'last_timestamp': '12345678.123',
            'details': None
        },
        {
            'name': 'TEST3_INFLUX',
            'status': 'NO_DATA',
            'last_timestamp': '12345678.123',
            'details': None
        }]
    expected_message = {
        'source': 'influxdb',
        'status_list': data
    }
    return data, expected_message


@pytest.fixture
def awx_client_data():
    data = {
        'name': 'TEST1_AWX_API',
        'status': 'OK',
        'last_timestamp': '12345678.123',
        'details': None
    }
    expected_message = {
        'source': 'awx_api',
        'status_list': [data]
    }
    return data, expected_message


@pytest.fixture
def awx_hook_data():
    data = [{
        'name': 'TEST1_AWX_WEB_HOOK',
        'status': 'OK',
        'last_timestamp': '12345678.123',
        'details': None
    }]

    expected_message = {
        'source': 'awx_web_hook',
        'status_list': data
    }
    return data, expected_message


@pytest.fixture(params=[InfluxSource, AWXApiSource, AWXWebHookSource])
def source_data(request, influx_source_data, awx_client_data, awx_hook_data):
    source = request.param
    if source == InfluxSource:
        return InfluxSource, influx_source_data
    elif source == AWXApiSource:
        return AWXApiSource, awx_client_data
    elif source == AWXWebHookSource:
        return AWXWebHookSource, awx_hook_data
    else:
        raise ValueError


@pytest.fixture
async def bot_alert_queue():
    queue = asyncio.Queue(1)
    return queue


@pytest.fixture
async def bot_silent_queue():
    queue = asyncio.Queue(1)
    return queue


@pytest.fixture
async def patched_bot(service, stop_event, bot_alert_queue: Queue, bot_silent_queue: Queue):
    bot = BotRunner(service, stop_event)

    async def _alert(a):
        await asyncio.wait_for(bot_alert_queue.put(a), .1)

    async def _silent(a):
        await asyncio.wait_for(bot_silent_queue.put(a), .1)

    bot.alert = _alert
    bot.silent = _silent
    asyncio.create_task(bot.start())
    await asyncio.sleep(.5)
    yield bot
    bot.stop_event.set()
    for queue in [bot_alert_queue, bot_silent_queue]:
        while not queue.empty():
            queue.get_nowait()
            queue.task_done()


@pytest.fixture
def chat_id():
    return f'{randrange(-0xffffffff, 0xffffffff)}'
