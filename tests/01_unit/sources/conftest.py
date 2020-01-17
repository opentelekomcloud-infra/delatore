import asyncio
from datetime import datetime

import pytest

from delatore.emoji import Emoji
from delatore.sources.awx_api import AWXApiClient, TIMESTAMP_FORMAT, single_template_filter
from tests.helpers import random_awx_data, random_influx_data, random_template_data


def _now():
    return datetime.now().strftime(TIMESTAMP_FORMAT)


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
    message = random_awx_data()

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
    message = random_influx_data()
    ideal_message = ('** From InfluxDB **\n'
                     f'`LB_LOAD` :    {Emoji.SUCCESS} `{message["LB_LOAD"]}`\n'
                     f'`LB_DOWN` :    {Emoji.FAILED} `{message["LB_DOWN"]}`\n'
                     f'`SCSI_HDD_TEST` :    {Emoji.NO_DATA} `{message["SCSI_HDD_TEST"]}`\n'
                     f'`RDS_TEST` :    {Emoji.SUCCESS} `{message["RDS_TEST"]}`')
    return message, ideal_message


@pytest.fixture
def template_status_obj():
    return random_template_data()


@pytest.fixture
def template_status_msg(template_status_obj):
    return rf'❌   —   `{template_status_obj.name}`  \(`12.12.19 11:04`\)'
