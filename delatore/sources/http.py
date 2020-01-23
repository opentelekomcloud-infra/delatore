import logging
from abc import ABC
from asyncio import Queue

from aiohttp import web
from aiohttp.web_request import Request
from apubsub.client import Client

from .base import Source
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

    def __init__(self, client: Client, polling_interval=10, request_timeout=10.0):
        super().__init__(client,
                         ignore_duplicates=True,
                         polling_interval=polling_interval,
                         request_timeout=request_timeout)
        app = web.Application()
        app.add_routes([web.get('/', ok)])
        self.app = app
        self.port = self.config.params['port']
        self.runner = web.AppRunner(self.app)
        self.site = None

    async def start(self, stop_event):
        """Start server coroutine"""
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, port=self.port)
        await self.site.start()
        LOGGER.debug('Web server started on port %s', self.port)
        await super().start(stop_event)
        await self.runner.cleanup()

    async def stop(self):
        await self.site.stop()


AWX_LISTENER_EMOJI_MAP = {
    '`failed`': Emoji.FAILED,
    '`running`': Emoji.RUNNING,
    '`success`': Emoji.SUCCESS,
    '`cancelled`': Emoji.CANCELED
}


class AWXWebHookSource(HttpListenerSource):
    """HTTP listener for AWX web hooks"""

    CONFIG_ID = 'awx_web_hook'

    @classmethod
    def convert(cls, data: dict) -> str:
        data.pop('From', None)
        text = convert(data).strip()
        text = '* From Ansible Tower *\n' + replace_emoji(text, AWX_LISTENER_EMOJI_MAP)
        return text

    def __init__(self, client):
        super().__init__(client,
                         polling_interval=10,  # checking input queue interval
                         request_timeout=.1)  # checking input queue timeout
        self.app.add_routes([
            web.post('/notifications', self.notifications)
        ])
        self.updates = Queue()

    async def notifications(self, request: web.Request):
        await self.updates.put(await request.json())
        return web.Response(text='OK')

    async def get_update(self):
        return await self.updates.get()
