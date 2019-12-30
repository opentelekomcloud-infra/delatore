import logging
from abc import ABC
from threading import Thread

from flask import Flask, request

from .base import Source
from ..emoji import Emoji, replace_emoji
from ..json2mdwn import convert

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)


class HttpListenerSource(Source, ABC):
    """HTTP listener"""

    def __init__(self, port):
        app = Flask(__name__)
        app.route('/')(lambda: 'OK')
        self.app = app
        self.port = port

    def start(self):
        """Start server in dedicated thread"""
        Thread(target=self.app.run, kwargs={'port': self.port}, daemon=True).start()
        LOGGER.info(f"{type(self).__name__} source started")


class AWXListenerSource(HttpListenerSource):
    EMOJI_MAP = {
        '`failed`': Emoji.FAILED,
        '`running`': Emoji.RUNNING,
        '`success`': Emoji.SUCCESS,
        '`cancelled`': Emoji.CANCELED
    }

    @classmethod
    def convert(cls, data: dict) -> str:
        data.pop('From', None)
        text = convert(data).strip()
        text = '** From Ansible Tower **\n' + replace_emoji(text, cls.EMOJI_MAP)
        return text

    PORT = 23834

    def __init__(self, port=PORT):
        super(AWXListenerSource, self).__init__(port)
        self.app.route('/notifications', methods=['POST'])(self.notifications)

    def notifications(self):
        self.updates = request.json
        return 'OK'
