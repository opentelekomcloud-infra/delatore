import pytest

from delatore.configuration import CSM_CHAT
from delatore.outputs.telegram.main import BotRunner


@pytest.fixture(scope='session')
def bot(service, stop_event):
    return BotRunner(service, stop_event)


async def send_and_remove(_bot, text):
    message = await _bot.silent(text)
    await _bot.remove(CSM_CHAT, message.message_id)


@pytest.mark.asyncio
async def test_send_message(bot):
    await send_and_remove(bot, 'test post to chat')


@pytest.mark.asyncio
async def test_influx_message_sending(bot, influxdb):
    status = {'TEST': 'OK'}
    message_converted = influxdb.convert(status)
    await send_and_remove(bot, message_converted)
