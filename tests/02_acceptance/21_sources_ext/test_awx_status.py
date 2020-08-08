import asyncio
import json

import pytest
from apubsub.client import Client

from delatore.sources.awx_api import NO_TEMPLATE_PATTERN, single_template_filter
from tests.helpers import random_string

TEMPLATE_NAME = 'csm_scenario 1.5 (native)'
pytestmark = pytest.mark.asyncio


async def test_get_data(awx_client):
    _filter = single_template_filter(TEMPLATE_NAME)
    single = await awx_client.get_templates(_filter)
    assert len(single) == 1
    message = awx_client.convert(single, TEMPLATE_NAME)
    assert message['source'] == awx_client.CONFIG_ID
    assert len(message['status_list']) == 1
    status = message['status_list'][0]
    assert all(key in status for key in ['name', 'status', 'timestamp'])  # FIXME: WUT!?


@pytest.mark.parametrize('depth', [3, 5])
async def test_get_data_with_depth(awx_client, depth):
    _filter = single_template_filter(TEMPLATE_NAME)
    container = await awx_client.get_templates(_filter, depth)
    assert len(container) == depth
    message = awx_client.convert(container, TEMPLATE_NAME)
    assert message['source'] == awx_client.CONFIG_ID
    assert len(message['status_list']) == depth


async def test_get_all_scenarios(awx_client):
    _filter = single_template_filter(TEMPLATE_NAME)
    single, multiple = await asyncio.gather(
        awx_client.get_templates(_filter),
        awx_client.get_templates(),
    )
    assert single[0] in multiple


async def test_get_not_existing_scenario(awx_client):
    _filter = single_template_filter(random_string())
    single = await awx_client.get_templates(_filter)
    assert single == []


@pytest.mark.parametrize('message', ['csm_scenario 1.5 (native);1', 'csm_delatore;1'])
async def test_trigger_from_loop(awx_client, pub: Client, sub: Client, message):
    await sub.subscribe(awx_client.TOPICS.changes)
    await asyncio.sleep(.2)
    await pub.publish(awx_client._params.topic_in, message)
    response = await sub.get(5)
    assert response is not None


async def test_trigger_empty_from_loop(awx_client, pub: Client, sub: Client):
    await sub.subscribe(awx_client.TOPICS.changes)
    await asyncio.sleep(.2)
    template_name = random_string()
    await pub.publish(awx_client._params.topic_in, f'{template_name};{1}')
    response = await sub.get(5)
    no_template = {'source': "awx_api", "error": NO_TEMPLATE_PATTERN.format(template_name)}
    assert json.loads(response) == no_template
