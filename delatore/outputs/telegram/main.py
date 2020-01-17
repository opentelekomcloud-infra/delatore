import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import Message, ParseMode
from apubsub import Service

from .parsing import CommandParsingError, parse_command
from ...configuration import BOT_CONFIG, CSM_CHAT
from ...sources import AWXApiClient, AWXListenerSource, InfluxSource

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

SOURCE_POLLING_INTERVAL = 2
STOP_EVENT = asyncio.Event()
STATUS = 'status'
IN_TOPICS = [
    InfluxSource.TOPIC,  # pylint: disable=no-member
    AWXApiClient.TOPIC,  # pylint: disable=no-member
    AWXListenerSource.TOPIC,  # pylint: disable=no-member
]


def _not_in_current_loop(smth):
    return (smth is None) or (asyncio.get_event_loop() != smth.loop)


class BotRunner:
    """Bot runner"""

    def __init__(self, msg_service: Service, stop_event: asyncio.Event):
        self.client = msg_service.get_client()
        self.stop_event = stop_event
        self.chat_id = CSM_CHAT
        self._bot = None
        self._dispatcher = None

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
            LOGGER.warning('No dispatcher in current event loop. Create dispatcher.')
            self._dispatcher = Dispatcher(self.bot)
            self._dispatcher.message_handler(commands=[STATUS])(self.handle_status)
        return self._dispatcher

    async def handle_status(self, message: Message):
        try:
            source, template_name, count = parse_command(message.text)
            await self.client.publish(AWXApiClient.TOPIC_IN, template_name)
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

    async def _start_posting(self):
        await self.client.start_consuming()
        await asyncio.wait([
            self.client.subscribe(topic) for topic in IN_TOPICS
        ])
        await self.alert('__Bot started__')
        async for message in self.client.get_iter():
            await self.alert(message)
            if self.stop_event.is_set():
                self.client.stop_getting()

    async def _shutdown(self):
        self.dispatcher.stop_polling()
        await self.dispatcher.storage.close()
        await self.dispatcher.storage.wait_closed()
        await self.dispatcher.bot.close()

    async def _start_polling(self):
        self.dispatcher.stop_polling()
        try:
            LOGGER.info('Start polling...')
            await self.dispatcher.start_polling()
        finally:
            await self._shutdown()

    async def start(self):
        """Start bot activities"""
        await asyncio.wait([
            self._start_polling(),
            self._start_posting(),
        ])


async def start_bot(message_service: Service, stop_event: asyncio.Event):
    """Start bot polling"""
    await BotRunner(message_service, stop_event).start()
