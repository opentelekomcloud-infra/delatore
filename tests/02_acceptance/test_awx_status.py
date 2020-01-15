import asyncio
import re

import pytest

from delatore.emoji import Emoji

TEMPLATE_NAME = 'Scenario 1.5'
__RE_DATE_TIME = r'(\d{2}\.){2}\d{2}\s\d{2}:\d{2}'
__RE_AWX_EMOJI = r''.join([Emoji.NO_DATA, Emoji.SUCCESS, Emoji.FAILED])
RE_STATUS = re.compile(r'[%s]\s+—\s+`[\w\s\d.]+`\s+\\\(`%s`\\\)' % (__RE_AWX_EMOJI, __RE_DATE_TIME))


@pytest.mark.asyncio
async def test_get_data(awx_client):
    message = await awx_client.create_status_message(template=TEMPLATE_NAME)
    assert RE_STATUS.findall(message), message


@pytest.mark.asyncio
async def test_get_all_scenarios(awx_client):
    single, multiple = await asyncio.gather(
        awx_client.create_status_message(template=TEMPLATE_NAME),
        awx_client.create_status_message(),
    )
    assert single in multiple
