import asyncio
import os
from random import choice

import pytest
from apubsub import Service

from delatore.emoji import Emoji
from delatore.sources import AWXApiSource, AWXWebHookSource, InfluxSource
from delatore.sources.awx_api import TemplateStatus
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
    data = {
        'From': 'InfluxDB',
        'LB_LOAD': 'OK',
        'LB_DOWN': 'FAIL',
        'SCSI_HDD_TEST': 'NO_DATA',
        'RDS_TEST': 'OK'
    }
    expected_message = ('*From InfluxDB*\n'
                        f'`LB_LOAD` :    {Emoji.SUCCESS} `{data["LB_LOAD"]}`\n'
                        f'`LB_DOWN` :    {Emoji.FAILED} `{data["LB_DOWN"]}`\n'
                        f'`SCSI_HDD_TEST` :    {Emoji.NO_DATA} `{data["SCSI_HDD_TEST"]}`\n'
                        f'`RDS_TEST` :    {Emoji.SUCCESS} `{data["RDS_TEST"]}`')
    return data, expected_message


@pytest.fixture
def awx_client_data():
    data = [TemplateStatus(
        name=f'{random_string(10)} 1',
        last_run_timestamp=current_timestamp(),
        last_status='successful',
        playbook=f'templates/{random_string(5)}.yaml'
    )]
    cur_date = current_timestamp('%d.%m.%y %H:%M')
    expected_message = '* AWX scenarios status: *\n' + rf'✅   —   `{data[0].name}`  \(`{cur_date}`\)'
    return data, expected_message


@pytest.fixture
def awx_hook_data():
    data = {
        'From': 'Ansible Tower',
        'test_job_id': random_with_length(3),
        'test_name': f'Test Send Message {random_string(4)}',
        'status': 'failed',
        'test_url': f'https://{random_string()}.{random_string(3)}',
        'test_dict': {
            'test': {
                'failed': choice([True, False]),
                'changed': random_with_length(1),
                'ok': random_with_length(2),
            }
        }
    }

    expected_message = ('* From Ansible Tower *\n'
                        f'Test Job Id :    `{data["test_job_id"]}`\n'
                        f'Test Name :    `{data["test_name"]}`\n'
                        f'Status :    ❌ `{data["status"]}`\n'
                        f'Test Url :    `{data["test_url"]}`\n'
                        'Test Dict :\n'
                        '    Test :\n'
                        f'        Failed :    `{data["test_dict"]["test"]["failed"]}`\n'
                        f'        Changed :    `{data["test_dict"]["test"]["changed"]}`\n'
                        f'        Ok :    `{data["test_dict"]["test"]["ok"]}`')
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
