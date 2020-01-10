import os
import string
from random import choice, randint, randrange

import pytest

from delatore.bot import bot
from delatore.configuration import CSM_CHAT
from delatore.emoji import Emoji
from delatore.sources import InfluxSource
from delatore.sources.awx_api import TemplateStatus


@pytest.fixture
def cleanup_message():
    yield
    if bot.last_message_id is not None:
        bot.delete_message(CSM_CHAT, bot.last_message_id)


@pytest.fixture
def influxdb():
    return InfluxSource()


def random_with_length(length):
    range_start = 10 ** (length - 1)
    range_end = (10 ** length) - 1
    return randint(range_start, range_end)


def random_string(length=10):
    letters = string.ascii_lowercase
    return ''.join(choice(letters) for _ in range(length))


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

    ideal_message = f"""** From Ansible Tower **
Test Job Id :    `{message['test_job_id']}`
Test Name :    `{message['test_name']}`
Status :    ❌ `{message['status']}`
Test Url :    `{message['test_url']}`
Test Dict :
    Test :
        Failed :    `{message['test_dict']['test']['failed']}`
        Changed :    `{message['test_dict']['test']['changed']}`
        Ok :    `{message['test_dict']['test']['ok']}`"""
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

    ideal_message = f"""** From InfluxDB **
`LB_LOAD` :    {Emoji.SUCCESS} `{message['LB_LOAD']}`
`LB_DOWN` :    {Emoji.FAILED} `{message['LB_DOWN']}`
`SCSI_HDD_TEST` :    {Emoji.NO_DATA} `{message['SCSI_HDD_TEST']}`
`RDS_TEST` :    {Emoji.SUCCESS} `{message['RDS_TEST']}`"""
    return message, ideal_message


@pytest.fixture
def template_status():
    obj = TemplateStatus(name='Scenario 1',
                         last_run_timestamp='2019-12-12T11:04:55.33Z',
                         last_status='failed',
                         playbook='playbook')
    message = f'❌   —   `{obj.name}`  (`12.12.19 11:04`)'
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

@pytest.fixture
def config_file(token, chat_id, influx_password, awx_auth_token):
    base_path = './tmp'
    os.makedirs(base_path, exist_ok=True)
    file_path = os.path.abspath(f'{base_path}/cfg.ini')
    with open(file_path, 'w+') as cfg:
        cfg.write(f'[DEFAULT]\ntoken = {token}\nchat_id = {chat_id}\ninflux_password = {influx_password}\nawx_auth_token = {awx_auth_token}')
    yield file_path
    os.remove(file_path)
    os.rmdir(base_path)


@pytest.fixture
def empty_env_vars():
    env_vars = {var: os.getenv(var) for var in ['token', 'chat_id']}
    for var in env_vars:
        os.environ.pop(var, None)
    yield
    for var, val in env_vars.items():
        if val:
            os.environ[var] = val
