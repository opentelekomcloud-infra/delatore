import asyncio
import re

import pytest
from apubsub.client import Client

from delatore.emoji import Emoji
from delatore.sources.awx_api import single_template_filter, NO_TEMPLATE_PATTERN
from tests.helpers import random_string

TEMPLATE_NAME = 'Scenario 1.5'
__RE_DATE_TIME = r'(\d{2}\.){2}\d{2}\s\d{2}:\d{2}'
__RE_AWX_EMOJI = r''.join([Emoji.NO_DATA, Emoji.SUCCESS, Emoji.FAILED])
RE_STATUS = re.compile(r'[%s]\s+—\s+`[\w\s\d.]+`\s+\\\(`%s`\\\)' % (__RE_AWX_EMOJI, __RE_DATE_TIME))

pytestmark = pytest.mark.asyncio


async def test_get_data(awx_client):
    _filter = single_template_filter(TEMPLATE_NAME)
    single = await awx_client.get_templates(_filter)
    assert len(single) == 1
    message = awx_client.convert(single)
    assert RE_STATUS.findall(message), message


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
    await asyncio.sleep(.1)
    await pub.publish(awx_client.TOPIC_IN, TEMPLATE_NAME)
    response = await sub.get(5)
    assert response is not None


async def test_trigger_empty_from_loop(awx_client, pub: Client, sub: Client):
    await sub.subscribe(awx_client.TOPIC)
    await asyncio.sleep(.1)
    template_name = random_string()
    await pub.publish(awx_client.TOPIC_IN, template_name)
    response = await sub.get(5)
    no_template = NO_TEMPLATE_PATTERN.format(template_name)
    assert response == f'* AWX scenarios status: *\n`{no_template}`'
