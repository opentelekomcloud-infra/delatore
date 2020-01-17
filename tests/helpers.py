import os
import string
from random import choice, randint

from delatore.sources.awx_api import TemplateStatus


def random_with_length(length):
    range_start = 10 ** (length - 1)
    range_end = (10 ** length) - 1
    return randint(range_start, range_end)


def random_string(length=10):
    letters = string.ascii_lowercase
    return ''.join(choice(letters) for _ in range(length))


def generate_config(token, chat_id, influx_password, awx_auth_token, tmp_dir):
    file_path = os.path.abspath(f'{tmp_dir}/cfg.ini')
    with open(file_path, 'w+') as cfg:
        cfg.write('[DEFAULT]\n'
                  f'token = {token}\n'
                  f'chat_id = {chat_id}\n'
                  f'influx_password = {influx_password}\n'
                  f'awx_auth_token = {awx_auth_token}')
    return file_path


def random_template_data():
    return TemplateStatus(name='Scenario 1',
                          last_run_timestamp='2019-12-12T11:04:55.33Z',
                          last_status='failed',
                          playbook='playbook')


def random_influx_data():
    return {
        'From': 'InfluxDB',
        'LB_LOAD': 'OK',
        'LB_DOWN': 'FAIL',
        'SCSI_HDD_TEST': 'NO_DATA',
        'RDS_TEST': 'OK'
    }


def random_awx_data():
    return {
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
