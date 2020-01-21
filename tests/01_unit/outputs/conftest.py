import asyncio
import socket
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
        await asyncio.wait_for(bot_alert_queue.put(a), .1)

    async def _silent(a):
        await asyncio.wait_for(bot_silent_queue.put(a), .1)

    bot.alert = _alert
    bot.silent = _silent
    asyncio.create_task(bot.start())
    # wait for bot consumer to start
    await asyncio.sleep(.1)
    await asyncio.wait_for(asyncio.open_connection('localhost', bot.client.port), 5)
    yield bot
    bot.stop_event.set()
    for queue in [bot_alert_queue, bot_silent_queue]:
        while not queue.empty():
            queue.get_nowait()
            queue.task_done()
