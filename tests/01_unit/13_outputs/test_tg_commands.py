"""Testing of parsing command arguments"""
import asyncio
import json
from asyncio import Queue

import pytest
from aiogram.types import Chat, Message
from apubsub.client import Client

from delatore.outputs.telegram.parsing import CommandParsingError, parse_command
from delatore.sources import AWXApiSource
from tests.helpers import random_string


@pytest.mark.parametrize(['quo'], '\'\"')
def test_parse_quotted_message(quo):
    """Testing of parsing quotted message"""
    expected = ('awx', 'Scenario 1.5', 5)
    message = f'/status {expected[0]} {quo}{expected[1]}{quo} {expected[2]}'
    source, detailed, count = parse_command(message)
    assert (source, detailed, count) == expected


@pytest.mark.parametrize(('message', 'expected'),
                         [
                             ('/status awx \'Scenario 1.5\' 5', ('awx', 'Scenario 1.5', 5)),
                             ('/status awx', ('awx', None, 1)),
                             ('/status awx  "Destroy 1" ', ('awx', 'Destroy 1', 1))
                         ])
def test_parse_command(message, expected):
    """Testing of parsing command arguments"""
    source, detailed, count = parse_command(message)
    assert (source, detailed, count) == expected


@pytest.mark.parametrize('message',
                         [
                             '/status awx Destroy test host 5',
                             '/status awx Scenario 1.5',
                             '/status awx "Scenario 1" 2 some other arguments',
                         ])
def test_parse_err(message):
    """Testing of handling exceptions during parsing command arguments"""
    with pytest.raises(CommandParsingError):
        parse_command(message)


@pytest.mark.asyncio
async def test_src_to_bot(patched_bot, pub: Client, bot_alert_queue: Queue, source_data):
    source_cls, (_, message) = source_data
    message = json.dumps(message)
    await pub.publish(source_cls.TOPIC, message)
    try:
        await asyncio.wait_for(bot_alert_queue.get(), .5)
        bot_alert_queue.task_done()
    except asyncio.TimeoutError:
        raise AssertionError


@pytest.mark.parametrize('target', ['', random_string()])
@pytest.mark.asyncio
async def test_bot_status_awx(patched_bot, sub: Client, chat_id, target):
    await sub.subscribe(AWXApiSource.params().topic_in)
    await asyncio.sleep(.05)
    message_text = f'/status awx {target}'
    await patched_bot.handle_status(Message(text=message_text, chat=Chat(id=chat_id)))
    data = await sub.get(.1)
    assert data == target


def patched_message(text, chat_id):
    resp_queue = Queue()
    message = Message(text=text, chat=chat_id)

    async def _answer(txt, *_, **__):
        resp_queue.put_nowait(txt)

    message.answer = _answer
    return message, resp_queue


@pytest.mark.parametrize('cmd', [
    f'/status {random_string()}',
    f'/status {random_string()} {random_string()}',
    f'/status'])
@pytest.mark.asyncio
async def test_bot_invalid_cmd(patched_bot, chat_id, cmd):
    message, answer_queue = patched_message(cmd, chat_id)
    await patched_bot.handle_status(message)
    response = answer_queue.get_nowait()
    assert response
