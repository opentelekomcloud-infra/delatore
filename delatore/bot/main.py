import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import Message, ParseMode

from .parsing import CommandParsingError, parse_command
from ..configuration import BOT_CONFIG
from ..sources import AWXApiClient, AWXListenerSource, InfluxSource
from ..sources.awx_api import NoSuchTemplate
from ..sources.base import Source

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

BOT = Bot(BOT_CONFIG.token, parse_mode=ParseMode.MARKDOWN_V2)
DISP = Dispatcher(BOT)

SOURCE_POLLING_INTERVAL = 2

STOP_EVENT = asyncio.Event()


async def alert(chat_id, message):
    """Send message to chat alerting users"""
    return await BOT.send_message(chat_id, message, disable_notification=False)


async def silent(chat_id, message):
    """Send message to chat without user alerting"""
    return await BOT.send_message(chat_id, message, disable_notification=True)


async def remove(chat_id, message_id):
    """Remove message from chat"""
    return await BOT.delete_message(chat_id, message_id)


# noinspection PyBroadException
async def _monitor_source(source: Source, stop_event: asyncio.Event):
    """Monitor resource and post updates to """

    async def __alert_on_update():
        while not stop_event.is_set():
            updates = source.updates  # read and clean updates field
            if updates:
                await alert(BOT_CONFIG.chat_id, source.convert(updates))
            await asyncio.sleep(SOURCE_POLLING_INTERVAL)

    scr_start = source.start(stop_event)
    alert_start = __alert_on_update()
    await asyncio.wait([scr_start, alert_start])


async def monitor_sources():
    source_coros = [_monitor_source(src(), STOP_EVENT) for src in [AWXListenerSource, InfluxSource]]
    STOP_EVENT.clear()
    await asyncio.wait(source_coros)


def stop_monitoring():
    STOP_EVENT.set()


STATUS = 'status'


@DISP.message_handler(commands=[STATUS])
async def handle_status(message: Message):
    try:
        source, template_name, count = parse_command(message.text)
    except CommandParsingError:
        return await message.answer('Invalid command. Please check command syntax')
    try:
        client = AWXApiClient()
        response = await client.create_status_message(template_name)
    except NoSuchTemplate:
        response = f'No template with name {template_name}'
    return await message.answer(response)
