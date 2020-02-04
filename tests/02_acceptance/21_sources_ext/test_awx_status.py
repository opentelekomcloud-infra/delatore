import asyncio
import json

import pytest
from apubsub.client import Client

from delatore.sources.awx_api import NO_TEMPLATE_PATTERN, single_template_filter
from tests.helpers import random_string

TEMPLATE_NAME = 'Scenario 1.5'
pytestmark = pytest.mark.asyncio


async def test_get_data(awx_client):
    _filter = single_template_filter(TEMPLATE_NAME)
    single = await awx_client.get_templates(_filter)
    assert len(single) == 1
    message = awx_client.convert(single, TEMPLATE_NAME)
    assert message['source'] == awx_client.CONFIG_ID
    assert len(message['status_list']) == 1
    status = message['status_list'][0]
    assert all(key in status for key in ['name', 'status', 'timestamp', 'details_url'])  # FIXME: WUT!?


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


async def test_trigger_from_loop(awx_client, pub: Client, sub: Client):
    await sub.subscribe(awx_client.TOPIC)
    await asyncio.sleep(.2)
    await pub.publish(awx_client.params().topic_in, TEMPLATE_NAME)
    response = await sub.get(5)
    assert response is not None


async def test_trigger_empty_from_loop(awx_client, pub: Client, sub: Client):
    await sub.subscribe(awx_client.TOPIC)
    await asyncio.sleep(.2)
    template_name = random_string()
    await pub.publish(awx_client.params().topic_in, template_name)
    response = await sub.get(5)
    no_template = {'source': "awx_api", "error": NO_TEMPLATE_PATTERN.format(template_name)}
    assert json.loads(response) == no_template
