import asyncio
import os
import threading
from asyncio.queues import Queue
from random import randrange
from uuid import uuid4

import pytest
from apubsub import Service

from delatore.outputs import AlertaRunner, BotRunner
from delatore.outputs.telegram.json2mdwn import convert
from delatore.sources import AWXApiSource, AWXWebHookSource, InfluxSource
from delatore.unified_json import convert_timestamp


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
def threading_stop_event():
    return threading.Event()


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
            'status': 'no_data',
            'timestamp': '2005-08-09T18:31:42',
            'details_url': None
        },
        {
            'name': 'TEST2_INFLUX',
            'status': 'fail',
            'timestamp': '2005-08-09T18:31:42',
            'details_url': None
        },
        {
            'name': 'LB_DOWN',
            'status': 'ok',
            'timestamp': '2005-08-09T18:31:42',
            'details_url': None
        }
    ]
    expected_message = {
        'source': 'influxdb',
        'status_list': [
            {
                'name': 'TEST1_INFLUX',
                'status': 'ok',
                'timestamp': '09.08.2005 18:31',
                'details_url': None
            },
            {
                'name': 'TEST2_INFLUX',
                'status': 'fail',
                'timestamp': '09.08.2005 18:31',
                'details_url': None
            },
            {
                'name': 'LB_DOWN',
                'status': 'ok',
                'timestamp': '09.08.2005 18:31',
                'details_url': None
            }
        ]
    }
    return data, expected_message


@pytest.fixture
def awx_client_data():
    data = [
        {
            'name': 'TEST1_AWX_API',
            'status': 'never updated',
            'last_job_run': '2005-08-09T18:31:42.20114Z',
            'details_url': None
        }
    ]
    expected_message = {
        'source': 'awx_api',
        'status_list':
            [
                {
                    'name': 'TEST1_AWX_API',
                    'status': 'no_data',
                    'timestamp': '09.08.2005 18:31',
                    'details_url': None
                }
            ]
    }
    return data, expected_message


@pytest.fixture
def awx_hook_data():
    data = {
        'id': f'{uuid4()}',
        'name': 'TEST1_AWX_WEB_HOOK',
        'status': 'running',
        'started': '2005-08-09T18:31:42.201142+00:00',
        'url': None
    }

    expected_message = {
        'source': 'awx_web_hook',
        'status_list':
            [
                {
                    'name': 'TEST1_AWX_WEB_HOOK',
                    'status': 'running',
                    'timestamp': '09.08.2005 18:31',
                    'details_url': None
                }
            ]
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


@pytest.fixture(params=[InfluxSource])
def source_data_alerta(request, influx_source_data):
    source = request.param
    if source == InfluxSource:
        return InfluxSource, influx_source_data
    else:
        raise ValueError


@pytest.fixture(params=[InfluxSource])
def source_data_alerta_series(request, influx_source_data):
    source = request.param
    if source == InfluxSource:
        return InfluxSource, influx_source_data
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
async def patched_alerta(service, stop_event):
    alerta = AlertaRunner(service, stop_event)
    asyncio.create_task(alerta.start())
    await asyncio.sleep(.5)
    yield alerta
    alerta.stop_event.set()


@pytest.fixture
def chat_id():
    return f'{randrange(-0xffffffff, 0xffffffff)}'


@pytest.fixture
def json2mdwn_data():
    message = {
        'source': 'awx_web_hook',
        'status_list':
            [
                {
                    'name': 'TEST1_AWX_WEB_HOOK',
                    'status': 'running',
                    'timestamp': '2005-08-09T18:31:42',
                    'details_url': None
                }
            ]
    }
    actual = convert(message)
    expected = '*From awx\\_web\\_hook*\n🏃  —  TEST1\\_AWX\\_WEB\\_HOOK \\(`2005\\-08\\-09T18:31:42`\\)'
    return actual, expected


@pytest.fixture
def time_data():
    TIME_FORMAT_PATTERN = '%Y-%m-%dT%H:%M:%S.%fZ'
    received_date = '2005-08-09T18:31:42.123456Z'
    actual_date = convert_timestamp(received_date, TIME_FORMAT_PATTERN)
    return actual_date, received_date
