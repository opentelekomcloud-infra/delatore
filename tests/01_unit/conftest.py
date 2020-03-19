import os
from random import randrange

import pytest

from tests.helpers import generate_config, random_string


@pytest.fixture
def token():
    return f'{randrange(999999999):09}:{random_string(35)}'


@pytest.fixture
def influx_password():
    return random_string(30)


@pytest.fixture
def awx_auth_token():
    return random_string(30)


@pytest.fixture
def alerta_api_key():
    return random_string(30)


@pytest.fixture
def alerta_service():
    return random_string(10)


@pytest.fixture
def config_file(token, chat_id, influx_password, awx_auth_token, alerta_api_key, alerta_service, tmp_dir):
    file_path = generate_config(token,
                                chat_id,
                                influx_password,
                                awx_auth_token,
                                alerta_api_key,
                                alerta_service,
                                tmp_dir)
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
