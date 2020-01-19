import asyncio
import logging
import threading
from threading import Thread

from aiogram import Bot, Dispatcher
from aiogram.types import Message, ParseMode
from aiogram.utils import executor
from apubsub import Service

from .parsing import CommandParsingError, parse_command
from ...configuration import BOT_CONFIG
from ...sources import AWXApiSource, AWXWebHookSource, InfluxSource

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

STATUS = 'status'
IN_TOPICS = [
    InfluxSource.TOPIC,  # pylint: disable=no-member
    AWXApiSource.TOPIC,  # pylint: disable=no-member
    AWXWebHookSource.TOPIC,  # pylint: disable=no-member
]


def _not_in_current_loop(smth):
    return (smth is None) or (asyncio.get_event_loop() != smth.loop)


class BotRunner:
    """Bot runner wrapper"""

    _bot: Bot = None
    _dispatcher: Dispatcher = None

    def __init__(self, msg_service: Service, stop_event: threading.Event):
        self.client = msg_service.get_client()
        self.stop_event = stop_event
        self.chat_id = BOT_CONFIG.chat_id

    @property
    def bot(self):
        """Return bot instance"""
        if _not_in_current_loop(self._bot):
            LOGGER.warning('No bot in current event loop. Create bot.')
            self._bot = Bot(BOT_CONFIG.token, parse_mode=ParseMode.MARKDOWN_V2)
        return self._bot

    @property
    def dispatcher(self):
        if _not_in_current_loop(self._dispatcher):
            LOGGER.warning('No dispatcher in current event loop. Create bot.')
            self._dispatcher = Dispatcher(self.bot)
            self._dispatcher.message_handler(commands=[STATUS])(self.handle_status)
        return self._dispatcher

    async def handle_status(self, message: Message):
        try:
            source, template_name, count = parse_command(message.text)
            await self.client.publish(AWXApiSource.TOPIC_IN, template_name)
        except CommandParsingError:
            await message.answer('Invalid command. Please check command syntax')

    async def alert(self, message):
        """Send message to chat alerting users"""
        return await self.bot.send_message(self.chat_id, message, disable_notification=False)

    async def silent(self, message):
        """Send message to chat without user alerting"""
        return await self.bot.send_message(self.chat_id, message, disable_notification=True)

    async def remove(self, message_id):
        """Remove message from chat"""
        return await self.bot.delete_message(self.chat_id, message_id)

    async def start_posting(self):
        """Start posting updates to channel"""
        await self.client.start_consuming()
        await asyncio.wait([
            self.client.subscribe(topic) for topic in IN_TOPICS
        ])
        await self.silent('__Bot started__')
        async for message in self.client.get_iter():
            await self.alert(message)
            if self.stop_event.is_set():
                self.client.stop_getting()

    async def start(self):
        """Start bot"""

        def _start_polling():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            executor.start_polling(self.dispatcher, loop=loop)

        thr = Thread(target=_start_polling)
        thr.start()
        await self.start_posting()
