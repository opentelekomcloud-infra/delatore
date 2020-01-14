import asyncio
import logging
from threading import Thread
from typing import Dict

from telebot import TeleBot
from telebot.apihelper import ApiException
from telebot.types import Message

from .parsing import CommandParsingError, parse_command
from ..configuration import BOT_CONFIG
from ..helpers import log_errors
from ..sources import AWXApiClient, AWXListenerSource, InfluxSource
from ..sources.awx_api import NoSuchTemplate
from ..sources.base import Source

MARKDOWN = "Markdown"

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)


class DelatoreBot(TeleBot):
    """TeleBot tweaked for delatore"""

    SOURCE_POLLING_INTERVAL = 10
    TG_POLLING_INTERVAL = 0.5

    last_message_id = None

    sources: Dict[str, Source] = None

    def __init__(self, *args, **kwargs):
        self.sources = {
            "AWX": AWXListenerSource(),
            "Influx": InfluxSource(),
        }
        super().__init__(*args, **kwargs)

    def alert(self, chat, text):
        """Send message with channel notifying"""
        return self.send_message(chat, text, disable_notification=False)

    def silent(self, chat, text):
        """Send message without notifying channel"""
        return self.send_message(chat, text, disable_notification=True)

    def send_message(self, chat_id, text, disable_notification=False, **kwargs):
        """Send telegram message"""
        try:
            message = super().send_message(
                chat_id, text,
                parse_mode=MARKDOWN,
                disable_notification=disable_notification,
                **kwargs
            )
        except ApiException:
            LOGGER.exception("Message can't be sent:\nChat:%s\nMessage:\n%s", chat_id, text)
            return None
        bot.last_message_id = message.message_id
        return message.json

    async def _monitor_source(self, src_name):
        """Monitor resource and post updates to """
        source = self.sources[src_name]
        try:
            source.start()
        except Exception:  # pylint: disable=broad-except
            LOGGER.exception("Failed to init source `%s`", src_name)
            return
        while True:
            updates = source.updates  # red and clean updates field
            if updates:
                self.alert(BOT_CONFIG.chat_id, source.convert(updates))
            await asyncio.sleep(self.SOURCE_POLLING_INTERVAL)

    def monitor_sources(self):
        """Start monitoring of given sources as coroutines"""
        coroutines = [self._monitor_source(src) for src in self.sources]
        wait_future = asyncio.wait(coroutines)
        Thread(target=asyncio.run, args=(wait_future,), daemon=True).start()

    def start(self):
        """Start bot polling telegram API ignoring exceptions"""
        self.monitor_sources()
        self.infinity_polling(interval=self.TG_POLLING_INTERVAL)


bot = DelatoreBot(BOT_CONFIG.token)  # pylint: disable=invalid-name

STATUS = 'status'


@log_errors
@bot.message_handler(commands=[STATUS])
def handle_start_help(message: Message):
    try:
        source, template_name, count = parse_command(message.text)
    except CommandParsingError:
        response = bot.reply_to(message, 'Invalid command. Please check command syntax')
        return bot.alert(message.chat.id, response)
    try:
        response = AWXApiClient().create_status_message(template_name)
    except NoSuchTemplate:
        response = f'No template with name {template_name}'
    return bot.alert(message.chat.id, response)
