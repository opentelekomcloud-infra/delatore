"""Testing of parsing command arguments"""
import asyncio
from asyncio import Queue

import pytest
from apubsub.client import Client

from delatore.outputs.telegram.bot import IN_TOPICS
from delatore.outputs.telegram.parsing import CommandParsingError, parse_command
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
                             ('/status awx', ('awx', None, None)),
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


@pytest.mark.parametrize('topic', IN_TOPICS)
@pytest.mark.asyncio
async def test_src_to_bot(topic, patched_bot, pub: Client, bot_alert_queue: Queue):
    message = random_string()
    await pub.publish(topic, message)
    try:
        received = await asyncio.wait_for(bot_alert_queue.get(), .1)
        bot_alert_queue.task_done()
    except asyncio.TimeoutError:
        raise AssertionError
    assert message == received
