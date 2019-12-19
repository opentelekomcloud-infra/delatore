from abc import ABC
from threading import Thread

from flask import Flask, request

from .base import Source
from ..const import AWX_STATUSES, EMOJI_LIST
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

    @classmethod
    def _add_emoji(cls, text: str) -> str:
        for item in AWX_STATUSES:
            text = text.replace(AWX_STATUSES[item], AWX_STATUSES[item] + EMOJI_LIST[item])
        return text

    @classmethod
    def convert(cls, data: dict) -> str:
        text = convert(data)
        text = '* From Ansible Tower *\n' + text
        return cls._add_emoji(text)

    PORT = 23834

    def __init__(self, port=PORT):
        super(AWXSource, self).__init__(port)
        self.app.route('/notifications', methods=['POST'])(self.notifications)

    def notifications(self):
        self.updates = request.json
        return 'OK'
