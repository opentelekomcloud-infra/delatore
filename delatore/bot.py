import configparser

import requests

from delatore.const import AWX_STATUSES, EMOJI_LIST
from delatore.json2mdwn import convert


class Delatore:
    last_message_id = 0

    def __init__(self):
        self.config = configparser.ConfigParser()
        self.session = requests.session()
        self.config.read('../config/config.ini')
        self.bot_token = self.config['DEFAULT']['token']
        self.url = self.config['DEFAULT']['url'] + self.bot_token + '/'
        self.chat_id = self.config['DEFAULT']['chat_id']

    def send_message(self, text, disable_notification=False):
        answer = {
            'chat_id': self.chat_id,
            'text': convert_message(text),
            'parse_mode': 'Markdown',
            'disable_notification': disable_notification
        }
        response = self.session.post(self.url + 'sendMessage', json=answer)
        return response.json()

    def delete_message(self, chat_id, message_id):
        params = {
            'chat_id': chat_id,
            'message_id': message_id,
        }
        response = self.session.post(self.url + 'deleteMessage', params=params)
        return response


def convert_message(data):
    """
    Converts json-like object to Telegram supported Markdown
    :param data: dict
    :return: Markdown string
    """
    text = convert(data)
    if text.find('awx.'):
        text = '* From Ansible Tower *\n' + text
    return add_emoji(text)


def add_emoji(text):
    """
    Adds emoji to selected status
    :param text: str
    :return: Markdown String with emoji
    """
    if text.find('Ansible'):
        for item in AWX_STATUSES:
            if item == 'FAILED':
                text = text.replace(AWX_STATUSES[item], AWX_STATUSES[item] + EMOJI_LIST[item])
            elif item == 'RUNNING':
                text = text.replace(AWX_STATUSES[item], AWX_STATUSES[item] + EMOJI_LIST[item])
            elif item == 'SUCCESS':
                text = text.replace(AWX_STATUSES[item], AWX_STATUSES[item] + EMOJI_LIST[item])
        return text
