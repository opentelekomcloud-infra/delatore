import asyncio
from asyncio import Queue

import pytest
from aiogram.types import Chat, Message


def message_stub(message_text, chat_id):
    return Message(text=message_text, chat=Chat(id=chat_id))


@pytest.mark.asyncio
async def test_status_awx(patched_bot, awx_client, chat_id, bot_alert_queue: Queue):
    await patched_bot.handle_status(message_stub('/status awx', chat_id))
    try:
        await asyncio.wait_for(bot_alert_queue.get(), 5)
    except asyncio.TimeoutError:
        raise AssertionError
