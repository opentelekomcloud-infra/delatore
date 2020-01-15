import os
from random import choice, randrange

import pytest

from delatore.emoji import Emoji
from delatore.sources.awx_api import TemplateStatus
from tests.helpers import random_string, random_with_length


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


@pytest.fixture
def token():
    return f'{randrange(999999999):09}:{random_string(35)}'


@pytest.fixture
def chat_id():
    return f'{randrange(-0xffffffff, 0xffffffff)}'


@pytest.fixture
def influx_password():
    return random_string(30)


@pytest.fixture
def awx_auth_token():
    return random_string(30)


@pytest.fixture(scope='session')
def tmp_dir():
    base_path = './tmp'
    os.makedirs(base_path, exist_ok=True)
    yield base_path
    os.rmdir(base_path)


@pytest.fixture
def config_file(token, chat_id, influx_password, awx_auth_token, tmp_dir):
    file_path = os.path.abspath(f'{tmp_dir}/cfg.ini')
    with open(file_path, 'w+') as cfg:
        cfg.write('[DEFAULT]\n'
                  f'token = {token}\n'
                  f'chat_id = {chat_id}\n'
                  f'influx_password = {influx_password}\n'
                  f'awx_auth_token = {awx_auth_token}')
    yield file_path
    os.remove(file_path)


@pytest.fixture
def empty_env_vars():
    env_vars = {}
    for var in ['token', 'chat_id']:
        value = os.getenv(var)
        if value is not None:
            env_vars[var] = value
    for var in env_vars:
        os.environ.pop(var, None)
    yield
    os.environ.update(env_vars)


@pytest.fixture
def empty_config_file(tmp_dir):
    file_name = f'{tmp_dir}/empty.ini'
    with open(file_name, 'w+') as cfg:
        cfg.write('[DEFAULT]\n')
    yield file_name
    os.remove(file_name)
