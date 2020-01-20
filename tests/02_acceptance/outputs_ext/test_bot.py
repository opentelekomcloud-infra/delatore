import pytest


async def send_and_remove(_bot, text):
    message = await _bot.silent(text)
    await _bot.remove(message.message_id)


pytestmark = pytest.mark.asyncio


async def test_send_message(bot):
    await send_and_remove(bot, 'test post to chat')


async def test_source_message_sending(bot, source_data):
    source, (_, message) = source_data
    await send_and_remove(bot, message)
