import asyncio
from datetime import datetime
from random import choice

import pytest

from delatore.emoji import Emoji
from delatore.sources.awx_api import AWXApiClient, TIMESTAMP_FORMAT, TemplateStatus, single_template_filter
from tests.helpers import random_string, random_with_length


def _now():
    return datetime.now().strftime(TIMESTAMP_FORMAT)


@pytest.fixture
def template_status_obj():
    return TemplateStatus('Scn 3.5', _now(), 'b', 'playbooks/test.yaml')


@pytest.fixture
async def patched_awx_client(template_status_obj, service, stop_event):
    async def _get_templates(_, filters: dict = None) -> list:
        if filters == single_template_filter(''):
            raise KeyError
        return [{
            'name': template_status_obj.name,
            'last_job_run': template_status_obj.last_run_timestamp,
            'status': template_status_obj.last_status,
            'playbook': template_status_obj.playbook,
        }]

    client = AWXApiClient(service.get_client())
    client.get_templates = _get_templates
    loop = asyncio.get_running_loop()
    loop.create_task(client.start(stop_event, False))
    yield client
    stop_event.set()


@pytest.fixture
def awx_data():
    message = {
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

    ideal_message = ('** From Ansible Tower **\n'
                     f'Test Job Id :    `{message["test_job_id"]}`\n'
                     f'Test Name :    `{message["test_name"]}`\n'
                     f'Status :    ❌ `{message["status"]}`\n'
                     f'Test Url :    `{message["test_url"]}`\n'
                     'Test Dict :\n'
                     '    Test :\n'
                     f'        Failed :    `{message["test_dict"]["test"]["failed"]}`\n'
                     f'        Changed :    `{message["test_dict"]["test"]["changed"]}`\n'
                     f'        Ok :    `{message["test_dict"]["test"]["ok"]}`')
    return message, ideal_message


@pytest.fixture
def influx_data():
    message = {
        'From': 'InfluxDB',
        'LB_LOAD': 'OK',
        'LB_DOWN': 'FAIL',
        'SCSI_HDD_TEST': 'NO_DATA',
        'RDS_TEST': 'OK'
    }

    ideal_message = ('** From InfluxDB **\n'
                     f'`LB_LOAD` :    {Emoji.SUCCESS} `{message["LB_LOAD"]}`\n'
                     f'`LB_DOWN` :    {Emoji.FAILED} `{message["LB_DOWN"]}`\n'
                     f'`SCSI_HDD_TEST` :    {Emoji.NO_DATA} `{message["SCSI_HDD_TEST"]}`\n'
                     f'`RDS_TEST` :    {Emoji.SUCCESS} `{message["RDS_TEST"]}`')
    return message, ideal_message


@pytest.fixture
def template_status():
    obj = TemplateStatus(name='Scenario 1',
                         last_run_timestamp='2019-12-12T11:04:55.33Z',
                         last_status='failed',
                         playbook='playbook')
    message = rf'❌   —   `{obj.name}`  \(`12.12.19 11:04`\)'
    return obj, message
