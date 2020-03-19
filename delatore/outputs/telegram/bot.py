import asyncio
import json
import logging
import threading

from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.utils.markdown import escape_md
from apubsub import Service
from ocomone import Resources

from .parsing import CommandParsingError, parse_command
from ...configuration import OUTPUTS_CFG
from ...configuration.dynamic import DEFAULT_INSTANCE_CONFIG, InstanceConfig
from ...outputs.telegram.json2mdwn import convert
from ...sources import AWXApiSource

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

STATUS = 'status'
HELP = 'help'
TG_CONFIG = OUTPUTS_CFG['telegram_bot']
STATUS_TOPICS = {
    'awx': AWXApiSource.params().topic_in,
}

__MESSAGES_PATH = Resources(__file__, resources_dir='messages')


def _load_help():
    msg_path = __MESSAGES_PATH['help.md']
    with open(msg_path, encoding='utf-8') as msg_file:
        msg = ''
        for line in msg_file:
            msg += line
    return {HELP: msg}


MESSAGES = _load_help()


def _not_in_current_loop(smth):
    return (smth is None) or (asyncio.get_event_loop() != smth.loop)


async def handle_help_cmd(message: Message):
    """Handler for /help command"""
    log_msg(message)
    answer_message = MESSAGES[HELP]
    await message.answer(answer_message)


def log_msg(message: Message):
    """Add LOGGER message"""
    LOGGER.debug('Message received: %s in chat %s', message.text, message.chat)


class BotRunner:
    """Bot runner wrapper"""
    _bot: Bot = None
    _dispatcher: Dispatcher = None

    def __init__(self, msg_service: Service, stop_event: threading.Event,
                 config: InstanceConfig = DEFAULT_INSTANCE_CONFIG):
        self.client = msg_service.get_client()
        self.stop_event = stop_event
        self.config = config
        self.chat_id = config.chat_id

    @property
    def bot(self):
        """Return bot instance, create new if missing"""
        if _not_in_current_loop(self._bot):
            LOGGER.warning('No bot exist. Create bot.')
            self._bot = Bot(self.config.token,
                            parse_mode=TG_CONFIG.params['parse_mode'],
                            proxy=self.config.proxy)
        return self._bot

    @property
    def dispatcher(self):
        """Return dispatcher instance, create new if missing"""
        if _not_in_current_loop(self._dispatcher):
            LOGGER.warning('No dispatcher exist. Create dispatcher.')
            self._dispatcher = Dispatcher(self.bot)
            self._dispatcher.register_message_handler(handle_help_cmd, commands=[HELP])
            self._dispatcher.register_message_handler(self.handle_status, commands=[STATUS])
        return self._dispatcher

    async def handle_status(self, message: Message):
        """Handler for /status command"""
        log_msg(message)
        try:
            source, template_name, count = parse_command(message.text)  # pylint:disable=unused-variable
        except CommandParsingError:
            return await message.answer(escape_md('Invalid command. Please check command syntax'))
        if source in STATUS_TOPICS:
            return await self.client.publish(STATUS_TOPICS[source], template_name or '')
        return await message.answer(rf'Invalid source: `{escape_md(source)}`')

    async def alert(self, message):
        """Send message to chat alerting users"""
        LOGGER.debug('Message (alert) sent to the chat %s:\n %s', self.chat_id, message)
        return await self.bot.send_message(self.chat_id, message, disable_notification=False)

    async def silent(self, message):
        """Send message to chat without user alerting"""
        LOGGER.debug('Message (silent) sent to the chat %s:\n %s', self.chat_id, message)
        return await self.bot.send_message(self.chat_id, message, disable_notification=True)

    async def remove(self, message_id):
        """Remove message from chat"""
        LOGGER.debug('Message %s removed from chat %s', message_id, self.chat_id)
        return await self.bot.delete_message(self.chat_id, message_id)

    async def start_posting(self):
        """Start posting updates to channel"""
        await self.client.start_consuming()
        topics = TG_CONFIG.subscriptions
        await asyncio.wait([
            self.client.subscribe(topic) for topic in topics
        ])
        LOGGER.info('Bot subscribed to topics: %s', topics)
        await self.silent('__Bot started__')
        while not self.stop_event.is_set():
            # message consumed
            message = await self.client.get(.1)
            if message is not None:
                data = json.loads(message)
                try:
                    await self.alert(convert(data))  # check if TG response was 200
                except Exception:  # pylint:disable=broad-except
                    LOGGER.exception('Failed to send message %s', data)

    async def _stopper(self):
        while not self.stop_event.is_set():
            await asyncio.sleep(.1)
        self.client.stop_getting()
        self.dispatcher.stop_polling()
        await self.dispatcher.storage.close()
        await self.dispatcher.storage.wait_closed()
        await self.dispatcher.bot.close()
        await self.dispatcher.wait_closed()

    async def start(self):
        """Start bot"""
        await asyncio.wait([
            self.start_posting(),
            self.dispatcher.start_polling(),
            self._stopper(),
        ])
