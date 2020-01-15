import pytest

from delatore.bot import remove, silent
from delatore.configuration import CSM_CHAT


async def send_and_remove(text):
    message = await silent(CSM_CHAT, text)
    await remove(CSM_CHAT, message.message_id)


@pytest.mark.asyncio
async def test_send_message():
    await send_and_remove('test post to chat')


@pytest.mark.asyncio
async def test_influx_message_sending(influxdb):
    message = await influxdb.get_influx_statuses()
    message_converted = influxdb.convert(message)
    await send_and_remove(message_converted)
