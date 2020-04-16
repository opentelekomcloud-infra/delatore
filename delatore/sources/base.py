"""Base Source implementation"""

import asyncio
import json
import logging
from abc import ABC, ABCMeta, abstractmethod
from inspect import isabstract
from typing import Optional, Union

from apubsub.client import Client

from ..configuration import DEFAULT_INSTANCE_CONFIG, InstanceConfig, SOURCES_CFG
from ..configuration.static import SourceConfiguration

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
    instance_config: InstanceConfig

    def __init__(self, client: Client,
                 ignore_duplicates=True,
                 instance_config: InstanceConfig = DEFAULT_INSTANCE_CONFIG):
        self.client = client
        self.polling_interval = self.config.timings.polling_interval
        self.request_timeout = self.config.timings.request_timeout
        self.ignore_duplicates = ignore_duplicates
        self.instance_config = instance_config

    @abstractmethod
    async def get_update(self) -> Optional[dict]:
        """Get source update"""

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
            if _same_status(new, last) and self.ignore_duplicates:
                continue
            LOGGER.debug('New data received from source: %s\ndata:\n%s', name, new)
            json_message = json.dumps(new)
            await self.client.publish(self.TOPIC, json_message)
            last = new
            LOGGER.debug('Wait for new data for %s', self.polling_interval)
            await asyncio.sleep(self.polling_interval)


def _same_status(new: dict, last: dict) -> bool:
    if last is None:
        return False
    if new == last:
        return True
    this_statuses = {st['name']: st['status'] for st in new['status_list']}
    another_statuses = {st['name']: st['status'] for st in last['status_list']}
    return this_statuses == another_statuses
