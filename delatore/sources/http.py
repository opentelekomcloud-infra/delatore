import asyncio
import logging
from abc import ABC

from aiohttp import web
from aiohttp.web_request import Request

from .base import Source
from ..emoji import Emoji, replace_emoji
from ..json2mdwn import convert

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)


async def ok(_: Request):
    return web.Response(text='OK')


class HttpListenerSource(Source, ABC):
    """HTTP listener"""

    def __init__(self, port):
        app = web.Application()
        app.add_routes([web.get('/', ok)])
        self.app = app
        self.port = port

    async def start(self, stop_event):
        """Start server coroutine"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, port=self.port)
        await site.start()
        while not stop_event.is_set():
            await asyncio.sleep(.1)
        await runner.cleanup()


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
        self.app.add_routes([
            web.get('/notifications', self.notifications)
        ])

    async def notifications(self, request: web.Request):
        self.updates = await request.json()
        return web.Response(text='OK')
