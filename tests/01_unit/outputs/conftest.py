import asyncio
from asyncio import Queue

import pytest

from delatore.outputs.telegram import BotRunner


@pytest.fixture
async def bot_alert_queue():
    queue = asyncio.Queue(1)
    return queue


@pytest.fixture
async def bot_silent_queue():
    queue = asyncio.Queue(1)
    return queue


@pytest.fixture
async def patched_bot(service, stop_event, bot_alert_queue: Queue, bot_silent_queue: Queue):
    bot = BotRunner(service, stop_event)

    async def _alert(a):
        await bot_alert_queue.put(a)

    async def _silent(a):
        await bot_silent_queue.put(a)

    bot.alert = _alert
    bot.silent = _silent
    loop = asyncio.get_running_loop()
    loop.create_task(bot.start())
    await asyncio.sleep(.2)
    yield bot
    bot.stop_event.set()
    while not bot_alert_queue.empty():
        bot_alert_queue.get_nowait()
        bot_alert_queue.task_done()
    await bot_alert_queue.join()
