import pytest

from delatore.outputs.telegram.json2mdwn import convert


async def send_and_remove(_bot, text):
    message = await _bot.silent(text)
    await _bot.remove(message.message_id)


pytestmark = pytest.mark.asyncio


async def test_send_message(bot):
    await send_and_remove(bot, 'test post to chat')


async def test_source_message_sending(bot, source_data):
    source, (_, data) = source_data
    message = convert(data)
    await send_and_remove(bot, message)
