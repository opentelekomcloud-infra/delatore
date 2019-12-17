import gevent
from flask import Flask, request

from .base_source import BaseSource
from ..bot import Delatore


class HttpSource(BaseSource):

    def __init__(self, bot: Delatore, port=2346):
        super().__init__(bot)
        app = Flask(__name__)
        app.route("/")(self.index)
        app.route('/notifications', methods=['POST'])(self.awx_notifications)
        self.app = app
        self.port = port

    def index(self):
        return 'OK'

    def awx_notifications(self):
        response = request.get_json()
        self.bot.message_queue.append(response)
        return "OK"

    def run(self):
        gevent.spawn(self.app.run, port=self.port)
