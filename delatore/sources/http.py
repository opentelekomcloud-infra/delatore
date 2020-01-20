import logging
from abc import ABC
from asyncio import Queue

from aiohttp import web
from aiohttp.web_request import Request
from apubsub.client import Client

from .base import NoUpdates, Source
from ..emoji import Emoji, replace_emoji
from ..json2mdwn import convert

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)


async def ok(_: Request):
    """Send `OK` response"""
    return web.Response(text='OK')


class HttpListenerSource(Source, ABC):
    """HTTP listener"""

    # pylint: disable=abstract-method

    def __init__(self, port, client: Client):
        super().__init__(client, .1)
        app = web.Application()
        app.add_routes([web.get('/', ok)])
        self.app = app
        self.port = port

    async def start(self, stop_event, no_duplicates=True):
        """Start server coroutine"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, port=self.port)
        await site.start()
        await super().start(stop_event, no_duplicates)
        await runner.cleanup()


AWX_LISTENER_EMOJI_MAP = {
    '`failed`': Emoji.FAILED,
    '`running`': Emoji.RUNNING,
    '`success`': Emoji.SUCCESS,
    '`cancelled`': Emoji.CANCELED
}


class AWXWebHookSource(HttpListenerSource):
    """HTTP listener for AWX web hooks"""

    PORT = 23834
    TOPIC = 'AWX_WEB_HOOK'

    @classmethod
    def convert(cls, data: dict) -> str:
        data.pop('From', None)
        text = convert(data).strip()
        text = '* From Ansible Tower *\n' + replace_emoji(text, AWX_LISTENER_EMOJI_MAP)
        return text

    def __init__(self, client):
        super().__init__(self.PORT, client)
        self.app.add_routes([
            web.get('/notifications', self.notifications)
        ])
        self.updates = Queue()

    async def notifications(self, request: web.Request):
        await self.updates.put(await request.json())
        return web.Response(text='OK')

    async def get_update(self):
        if self.updates.empty():
            raise NoUpdates
        return await self.updates.get()
