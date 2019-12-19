import configparser

import requests

from .sources.http import AWXSource


class Delatore:
    sources_list = {'AWX': AWXSource()}
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
            'text': text,
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
