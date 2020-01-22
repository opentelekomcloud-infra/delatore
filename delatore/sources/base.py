"""Base Source implementation"""

import asyncio
import logging
from abc import ABC, ABCMeta, abstractmethod
from inspect import isabstract
from typing import Optional, Union

from apubsub.client import Client

from delatore.configuration import SOURCES_CFG
from delatore.configuration.static import SourceConfiguration

Json = Union[dict, list]

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)


class NoUpdates(Exception):
    """Raised when source has no updates"""


class SourceMeta(ABCMeta):
    """Source class meta setting up data from configuration"""

    CONFIG_ID: str
    TOPIC: str
    config: SourceConfiguration

    def __init__(cls, name, bases=(), dct=None):  # pylint:disable=redefined-builtin
        super().__init__(name, bases, dct)
        if not isabstract(cls):  # skip configuration for abstracts
            assert hasattr(cls, 'CONFIG_ID')
            cls.config = SOURCES_CFG[cls.CONFIG_ID]
            cls.TOPIC = cls.config.publishes


class Source(ABC, metaclass=SourceMeta):
    """Source API posting updates to """

    CONFIG_ID: str = NotImplemented

    client: Client
    config: SourceConfiguration

    def __init__(self, client: Client,
                 polling_interval=10.0,
                 request_timeout=10.0,
                 ignore_duplicates=True):
        self.client = client
        self.polling_interval = polling_interval
        self.request_timeout = request_timeout
        self.ignore_duplicates = ignore_duplicates

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
