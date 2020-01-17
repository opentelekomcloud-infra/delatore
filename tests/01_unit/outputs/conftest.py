import asyncio

import pytest

from delatore.outputs.telegram import BotRunner


@pytest.fixture
async def bot_buffer_queue():
    queue = asyncio.Queue()
    return queue


@pytest.fixture
async def patched_bot(service, stop_event, bot_buffer_queue: asyncio.Queue):
    bot = BotRunner(service, stop_event)

    async def _alert(a):
        await asyncio.wait_for(bot_buffer_queue.put(a), .01)

    bot.alert = _alert
    loop = asyncio.get_running_loop()
    loop.create_task(bot.start())
    await asyncio.sleep(.2)
    yield bot
    bot.stop_event.set()
    while not bot_buffer_queue.empty():
        bot_buffer_queue.get_nowait()
