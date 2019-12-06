import json

import requests
import configparser

from delatore.const import AWX_STATUSES, EMOJI_LIST
from delatore.json2mdwn import convert


class Delatore(object):

    def __init__(self):
        self.config = configparser.ConfigParser()
        self.session = requests.session()
        self.bot_parameters = self.read_config()

    def read_config(self):
        self.config.read('../config/config.ini')
        self.TG_BOT_TOKEN = self.config['DEFAULT']['token']
        self.URL = self.config['DEFAULT']['url'] + self.TG_BOT_TOKEN + '/'
        return self

    def convert_message(self, text):
        text = convert(text)
        if text.find('awx.'):
            text = '* From Ansible Tower *\n' + text
        return self.add_emoji(text)

    def get_chat_id(self):
        url = self.URL + 'getUpdates'
        response = self.session.get(url)
        return json.loads(response.text)['result'][-1]['message']['chat']['id']

    def send_message(self, chat_id, text):
        answer = {
            'chat_id': chat_id,
            'text': self.convert_message(text),
            'parse_mode': 'Markdown'
        }
        response = self.session.post(self.URL + 'sendMessage', json=answer)
        return response.json()

    def send_notification(self, text):
        self.send_message(self.get_chat_id(), text)

    def add_emoji(self, text):
        if text.find('Ansible'):
            for item in AWX_STATUSES:
                if item == 'FAILED':
                    text = text.replace(AWX_STATUSES[item], AWX_STATUSES[item] + EMOJI_LIST[item])
                elif item == 'RUNNING':
                    text = text.replace(AWX_STATUSES[item], AWX_STATUSES[item] + EMOJI_LIST[item])
                elif item == 'SUCCESS':
                    text = text.replace(AWX_STATUSES[item], AWX_STATUSES[item] + EMOJI_LIST[item])
            return text
