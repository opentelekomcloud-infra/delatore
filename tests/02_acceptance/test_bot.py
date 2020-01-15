import asyncio

import pytest

from delatore.bot import silent
from delatore.configuration import CSM_CHAT


@pytest.mark.asyncio
async def test_send_message():
    await silent(CSM_CHAT, 'test post to chat')


@pytest.mark.asyncio
async def test_influx_message_sending(influxdb):
    message = await influxdb.get_influx_statuses()
    message_converted = influxdb.convert(message)
    await silent(CSM_CHAT, message_converted)
