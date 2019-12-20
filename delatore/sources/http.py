from abc import ABC
from threading import Thread

from flask import Flask, request

from .base import Source
from ..emoji import Emoji, replace_emoji
from ..json2mdwn import convert


class HttpSource(Source, ABC):
    """HTTP listener"""

    def __init__(self, port):
        app = Flask(__name__)
        app.route('/')(lambda: 'OK')
        self.app = app
        self.port = port

    def run(self):
        Thread(target=self.app.run, kwargs={'port': self.port}).start()


class AWXSource(HttpSource):
    EMOJI_MAP = {
        '`failed`': Emoji.FAILED,
        '`running`': Emoji.RUNNING,
        '`success`': Emoji.SUCCESS,
        '`cancelled`': Emoji.CANCELED
    }

    @classmethod
    def convert(cls, data: dict) -> str:
        data.pop('From', None)
        text = convert(data)
        text = '** From Ansible Tower **\n' + replace_emoji(text, cls.EMOJI_MAP)
        return text.strip()

    PORT = 23834

    def __init__(self, port=PORT):
        super(AWXSource, self).__init__(port)
        self.app.route('/notifications', methods=['POST'])(self.notifications)

    def notifications(self):
        self.updates = request.json
        return 'OK'
