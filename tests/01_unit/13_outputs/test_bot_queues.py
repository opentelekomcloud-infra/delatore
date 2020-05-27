import asyncio
import json
from asyncio import Queue

import pytest
from apubsub.client import Client

pytestmark = pytest.mark.asyncio


async def test_src_to_bot(patched_bot, pub: Client, bot_alert_queue: Queue, source_data):
    source_cls, (_, message) = source_data
    message = json.dumps(message)
    await pub.publish(source_cls.TOPICS.changes, message)
    try:
        await asyncio.wait_for(bot_alert_queue.get(), 1.5)
        bot_alert_queue.task_done()
    except asyncio.TimeoutError:
        raise AssertionError


async def test_src_to_alerta(patched_alerta, pub: Client, bot_alert_queue: Queue, source_data_alerta):
    source, (_, message) = source_data_alerta
    message = json.dumps(message)
    await pub.publish(source.TOPICS.changes, message)
    try:
        await asyncio.wait_for(bot_alert_queue.get(), 1.5)
        bot_alert_queue.task_done()
    except asyncio.TimeoutError:
        raise AssertionError
