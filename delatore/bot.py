import requests
import telebot

from .configuration import BOT_CONFIG
from .sources.http import AWXSource

MARKDOWN = 'Markdown'


class Delatore:
    sources_list = {'AWX': AWXSource()}
    last_message_id = 0

    def __init__(self):
        self.session = requests.session()
        self.bot = telebot.TeleBot(BOT_CONFIG.token)

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
