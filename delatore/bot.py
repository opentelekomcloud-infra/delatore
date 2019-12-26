import requests
import telebot
from ocomone import Resources
from telebot.types import Message

from .configuration import BOT_CONFIG
from .sources import AwxApiClient, AWXSource

MARKDOWN = 'Markdown'


class Delatore:
    bot = telebot.TeleBot(BOT_CONFIG.token)
    sources_list = {'AWX': AWXSource()}
    last_message_id = 0

    def __init__(self):
        self.session = requests.session()

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

    @bot.message_handler(commands=['status'])
    def handle_start_help(self, message: Message):
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
            self.bot.send_message(message.chat.id, response)
