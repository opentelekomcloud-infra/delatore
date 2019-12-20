import string
from random import choice, randint

import pytest

from delatore.bot import CSM_CHAT, Delatore


@pytest.fixture
def bot():
    _bot = Delatore()
    yield _bot
    _bot.delete_message(CSM_CHAT, _bot.last_message_id)


def random_with_length(length):
    range_start = 10 ** (length - 1)
    range_end = (10 ** length) - 1
    return randint(range_start, range_end)


def random_string(length=10):
    letters = string.ascii_lowercase
    return ''.join(choice(letters) for i in range(length))


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
