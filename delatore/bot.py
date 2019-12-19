import configparser
from typing import NamedTuple

import requests
import telebot
from ocomone import Resources

from .sources.http import AWXSource

CONFIG = Resources(__file__, '../config')


class BotConfig(NamedTuple):
    """Bot configuration container"""
    token: str
    url: str
    chat_id: str


def __read_config():
    """Read configuration from configuration file"""
    config = configparser.ConfigParser()
    config.read(CONFIG['config.ini'])
    token = config['DEFAULT']['token']
    url = config['DEFAULT']['url'] + token + '/'
    chat_id = config['DEFAULT']['chat_id']
    return BotConfig(token, url, chat_id)


_BOT_CONFIG = __read_config()

CSM_CHAT = _BOT_CONFIG.chat_id
MARKDOWN = 'Markdown'


class Delatore:
    sources_list = {'AWX': AWXSource()}
    last_message_id = 0

    def __init__(self):
        self.session = requests.session()
        self.bot = telebot.TeleBot(_BOT_CONFIG.token)

    def start(self):
        """Start bot polling telegram API ignoring exceptions"""
        self.bot.infinity_polling(interval=0.5)

    def send_message(self, text, chat, disable_notification=False):
        """Send telegram message"""
        message = self.bot.send_message(
            chat, text,
            parse_mode=MARKDOWN,
            disable_notification=disable_notification)
        self.last_message_id = message.message_id
        return message.json

    def silent(self, text, chat):
        """Send message without notifying channel"""
        return self.send_message(text, chat, True)

    def alert(self, text, chat):
        """Send message with channel notifying"""
        return self.send_message(text, chat, False)

    def delete_message(self, chat_id, message_id):
        return self.bot.delete_message(chat_id, message_id)
