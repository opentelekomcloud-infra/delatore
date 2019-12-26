import re

import pytest

from delatore.emoji import Emoji
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
RE_STATUS = re.compile(r'[{0}]\s+—\s+`[\w\s\d.]+`\s+\(`[\w\d_]+\.ya?ml`\)'.format(
    "".join([Emoji.SUCCESS, Emoji.NO_DATA, Emoji.FAILED])
))


def test_get_data(awx_client):
    message = awx_client.create_status_message(template=TEMPLATE_NAME)
    print(5)
    assert RE_STATUS.findall(message), message


def test_get_all_scenarios(awx_client):
    single = awx_client.create_status_message(template=TEMPLATE_NAME)
    multiple = awx_client.create_status_message()
    print(multiple)
    assert single in multiple
