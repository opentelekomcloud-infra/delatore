import threading
import time
from typing import Dict, Type

import telebot
from telebot.types import Message

from .configuration import BOT_CONFIG
from .sources import AWXSource, AwxApiClient, InfluxSource
from .sources.base import Source

MARKDOWN = 'Markdown'


class DelatoreBot(telebot.TeleBot):
    """TeleBot tweaked for delatore"""

    POLLING_INTERVAL = 0.5

    last_message_id = None

    sources: Dict[str, Type[Source]] = None

    def __init__(self, *args, **kwargs):
        self.sources = {
            'AWX': AWXSource,
            'Influx': InfluxSource,
        }
        super().__init__(*args, **kwargs)

    def alert(self, text, chat):
        """Send message with channel notifying"""
        return self.send_message(text, chat, disable_notification=False)

    def silent(self, text, chat):
        """Send message without notifying channel"""
        return self.send_message(text, chat, True)

    def send_message(self, text, chat, disable_notification=False, **kwargs):
        """Send telegram message"""
        kwargs.pop('disable_notification', None)
        message = super().send_message(
            chat, text,
            parse_mode=MARKDOWN,
            disable_notification=disable_notification,
            **kwargs
        )
        bot.last_message_id = message.message_id
        return message.json

    def monitor_sources(self):
        """Start monitoring of given sources in dedicated thread"""

        def _mon(src):
            if isinstance(src, type):
                src = src()
            while True:
                updates = src.updates  # read and clean updates field
                if updates:
                    self.alert(src.convert(updates), BOT_CONFIG.chat_id)
                time.sleep(self.POLLING_INTERVAL)

        for source in self.sources.values():
            threading.Thread(target=_mon, args=(source,), daemon=True).start()

    def start(self):
        """Start bot polling telegram API ignoring exceptions"""
        self.monitor_sources()
        self.infinity_polling(interval=self.POLLING_INTERVAL)


bot = DelatoreBot(BOT_CONFIG.token)


@bot.message_handler(commands=['status'])
def handle_start_help(message: Message):
    # msg_text = "/status awx:scenario1 5"
    message_text: str = message.text
    _, *arguments = message_text.split(" ")
    if not arguments:
        return
    if len(arguments) > 1:
        count = int(arguments[1])
    else:
        count = 1
    target: list = arguments.pop(0).split(":")
    template = None
    if target[0] == 'awx':
        if len(target) > 1:
            template = target[1]
        response = AwxApiClient().create_status_message(template)
        bot.alert(message.chat.id, response)
