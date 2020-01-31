import calendar
import logging
import time
from abc import ABC
from asyncio import Queue
from traceback import format_exc
from typing import List

from aiohttp import web
from aiohttp.web_request import Request
from apubsub.client import Client

from .base import Source
from ..unified_json import Status, generate_status, generate_message, generate_error, convert_timestamp

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)


async def ok(_: Request):
    """Send `OK` response"""
    return web.Response(text='OK')


class HttpListenerSource(Source, ABC):
    """HTTP listener"""

    # pylint: disable=abstract-method

    def __init__(self, client: Client):
        super().__init__(client,
                         ignore_duplicates=True)
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


def switch_status(argument) -> Status:
    status = {
        'running': Status.RUNNING,
        'failed': Status.FAIL,
        'canceled': Status.CANCELED,
        'successful': Status.OK
    }
    return status.get(argument, 'Invalid status')


class AWXWebHookSource(HttpListenerSource):
    """HTTP listener for AWX web hooks"""

    CONFIG_ID = 'awx_web_hook'

    @classmethod
    def convert(cls, data: List[dict]) -> dict:
        data = data[0]
        try:
            status = generate_status(
                name=data['name'],
                status=switch_status(data['status']),
                timestamp=convert_timestamp(data['started']),
                details_url=data['url'],
            )
        except KeyError:
            return generate_error(cls.CONFIG_ID, format_exc(limit=10))
        return generate_message(cls.CONFIG_ID, [status])

    def __init__(self, client):
        super().__init__(client)
        self.app.add_routes([
            web.post('/notifications', self.notifications)
        ])
        self.updates = Queue()

    async def notifications(self, request: web.Request):
        await self.updates.put(await request.json())
        return web.Response(text='OK')

    async def get_update(self):
        return await self.updates.get()
