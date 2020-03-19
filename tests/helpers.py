import os
import string
from datetime import datetime
from random import choice, randint


def random_with_length(length):
    range_start = 10 ** (length - 1)
    range_end = (10 ** length) - 1
    return randint(range_start, range_end)


def random_string(length=10):
    letters = string.ascii_lowercase
    return ''.join(choice(letters) for _ in range(length))


def current_timestamp(fmt='%Y-%m-%dT%H:%M:%S.%fZ'):
    return datetime.now().strftime(fmt)


def generate_config(token, chat_id, influx_password, awx_auth_token, alerta_api_key, alerta_service, tmp_dir):
    file_path = os.path.abspath(f'{tmp_dir}/cfg.ini')
    with open(file_path, 'w+') as cfg:
        cfg.write('[DEFAULT]\n'
                  f'token = {token}\n'
                  f'chat_id = {chat_id}\n'
                  f'influx_password = {influx_password}\n'
                  f'awx_auth_token = {awx_auth_token}\n'
                  f'alerta_api_key = {alerta_api_key}\n'
                  f'alerta_service = {alerta_service}')
    return file_path
