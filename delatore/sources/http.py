import logging
from abc import ABC
from asyncio import Queue
from traceback import format_exc

from aiohttp import web
from aiohttp.web_request import Request
from apubsub.client import Client

from .awx_api import switch_awx_status
from .base import Source
from ..configuration import DEFAULT_INSTANCE_CONFIG
from ..unified_json import convert_timestamp, generate_error, generate_message, generate_status

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
WH_TIME_PATTERN = '%Y-%m-%dT%H:%M:%S.%f%z'


async def ok(_: Request):
    """Send `OK` response"""
    return web.Response(text='OK')


class HttpListenerSource(Source, ABC):
    """HTTP listener"""

    # pylint: disable=abstract-method

    def __init__(self, client: Client, instance_config=DEFAULT_INSTANCE_CONFIG):
        super().__init__(client,
                         ignore_duplicates=False,
                         instance_config=instance_config)
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


class AWXWebHookSource(HttpListenerSource):
    """HTTP listener for AWX web hooks"""

    CONFIG_ID = 'awx_web_hook'

    def __init__(self, client):
        super().__init__(client)
        self.app.add_routes([
            web.post('/notifications', self.notifications)
        ])
        self.updates = Queue()

    async def notifications(self, request: web.Request):
        data = await request.json()
        LOGGER.debug('Data from AWX: %s', data)
        await self.updates.put(data)
        return web.Response(text='OK')

    async def get_update(self):
        update = await self.updates.get()
        try:
            status = generate_status(
                name=update['name'],
                status=switch_awx_status(update['status']),
                timestamp=convert_timestamp(update['started'], WH_TIME_PATTERN),
                details_url=update['url'],
            )
        except KeyError:
            return generate_error(self.CONFIG_ID, format_exc(limit=10))
        return generate_message(self.CONFIG_ID, [status])
