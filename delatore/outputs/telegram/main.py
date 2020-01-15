import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import Message, ParseMode
from aiogram.utils import executor
from apubsub import Service

from .parsing import CommandParsingError, parse_command
from ...configuration import BOT_CONFIG, CSM_CHAT
from ...sources import AWXApiClient, AWXListenerSource, InfluxSource

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


STATUS = 'status'

IN_TOPICS = [
    InfluxSource.TOPIC,  # pylint: disable=no-member
    AWXApiClient.TOPIC,  # pylint: disable=no-member
    AWXListenerSource.TOPIC,  # pylint: disable=no-member
]


class BotRunner:
    """Bot runner"""

    def __init__(self, msg_service: Service, stop_event: asyncio.Event):
        self.client = msg_service.get_client()
        self.stop_event = stop_event
        self.client.get_all()  # clean up message queue

        for topic in IN_TOPICS:
            self.client.subscribe(topic)

        DISP.message_handler(commands=[STATUS])(self.handle_status)

    async def handle_status(self, message: Message):
        try:
            source, template_name, count = parse_command(message.text)
        except CommandParsingError:
            return await message.answer('Invalid command. Please check command syntax')
        self.client.publish(AWXApiClient.TOPIC_IN, template_name)

    async def start_posting(self):
        async for message in self.client.start_receiving():
            await alert(CSM_CHAT, message)
            if self.stop_event.is_set():
                self.client.stop_receiving()
            await asyncio.sleep(.1)


async def start_polling():
    executor.start_polling(DISP)


async def start_bot(message_service: Service, stop_event: asyncio.Event):
    """Start bot polling"""
    runner = BotRunner(message_service, stop_event)
    await asyncio.wait([
        runner.start_posting(),
        start_polling(),
    ])
