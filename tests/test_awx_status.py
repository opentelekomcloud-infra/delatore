import pytest

from delatore.json2mdwn import _normalize_key
from delatore.sources.awx_api import AwxApiClient


@pytest.fixture
def awx_client():
    client = AwxApiClient()
    return client


@pytest.fixture
def awx_client():
    client = AwxApiClient()
    return client


TEMPLATE_NAME = 'Scenario 1.5'


def test_get_data(awx_client):
    message = awx_client.create_status_message(template=TEMPLATE_NAME)
    print(message)
    assert TEMPLATE_NAME in message
    assert message.count(_normalize_key('name')) == 1
    assert message.count(_normalize_key('last_run_timestamp')) == 1
    assert message.count(_normalize_key('last_status')) == 1
    assert message.count(_normalize_key('playbook')) == 1


def test_get_all_scenarios(awx_client):
    single = awx_client.create_status_message(template=TEMPLATE_NAME)
    multiple = awx_client.create_status_message()
    assert single in multiple
