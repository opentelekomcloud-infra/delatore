from threading import Thread

from flask import Flask, request

from .base_source import Source


class HttpSource(Source):
    """HTTP listener"""

    def __init__(self, port):
        app = Flask(__name__)
        app.route('/')(lambda: 'OK')
        self.app = app
        self.port = port

    def run(self):
        Thread(target=self.app.run, kwargs={'port': self.port}).start()


class AWXSource(HttpSource):
    AWX_PORT = 23834

    def __init__(self, port=AWX_PORT):
        super(AWXSource, self).__init__(port)
        self.app.route("/notifications", methods=["POST"])(self.notifications)

    def notifications(self):
        self.updates = request.json
        return 'OK'
