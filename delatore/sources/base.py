"""Base Source implementation"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Optional, Union

from apubsub.client import Client

Json = Union[dict, list]

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)


class NoUpdates(Exception):
    """Raised when source has no updates"""


class Source(ABC):
    """Source API posting updates to """

    client: Client
    TOPIC: str

    def __init__(self, client: Client, polling_interval=10.0, request_timeout=10.0, ignore_duplicates=True):
        self.client = client
        self.polling_interval = polling_interval
        self.request_timeout = request_timeout
        self.ignore_duplicates = ignore_duplicates
        if not hasattr(self, 'TOPIC'):
            raise NotImplementedError(f'Source has no topic')

    @abstractmethod
    async def get_update(self) -> Optional[Json]:
        """Get source update"""

    @classmethod
    @abstractmethod
    def convert(cls, data: Json) -> str:
        """Converts json-like object to Telegram supported Markdown

        :param data: JSON dictionary or list
        :return: Markdown string
        """

    async def start(self, stop_event: asyncio.Event):
        """Start processing updates"""
        last = None
        name = type(self).__name__
        LOGGER.info('Source %s started', name)
        while not stop_event.is_set():
            try:
                new = await asyncio.wait_for(self.get_update(), self.request_timeout)
            except (asyncio.TimeoutError, NoUpdates):
                continue
            if new in [last, None] and self.ignore_duplicates:
                continue
            LOGGER.debug('New data received from source: %s\ndata:\n%s', name, new)
            md_message = self.convert(new)
            await self.client.publish(self.TOPIC, md_message)
            last = new
            LOGGER.debug('Wait for new data for %s', self.polling_interval)
            await asyncio.sleep(self.polling_interval)
