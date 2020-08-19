"""Base Source implementation"""

import asyncio
import json
import logging
from abc import ABC, ABCMeta, abstractmethod
from inspect import isabstract
from typing import NamedTuple, Optional, Union

from apubsub.client import Client

from ..configuration import DEFAULT_INSTANCE_CONFIG, InstanceConfig, SOURCES_CFG
from ..configuration.static import SourceConfiguration

Json = Union[dict, list]

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)


class NoUpdates(Exception):
    """Raised when source has no updates"""


class Topics(NamedTuple):
    changes: str
    info: str
    error: str

    @classmethod
    def with_prefix(cls, prefix: str):
        prefix = prefix.upper()
        return Topics(f'{prefix}_CHANGES', f'{prefix}_INFO', f'{prefix}_ERROR')


class SourceMeta(ABCMeta):
    """Source class meta setting up data from configuration"""

    CONFIG_ID: str
    TOPICS: Topics
    config: SourceConfiguration

    def __init__(cls, name, bases=(), dct=None):  # pylint:disable=redefined-builtin
        super().__init__(name, bases, dct)
        if not isabstract(cls):  # skip configuration for abstracts
            assert hasattr(cls, 'CONFIG_ID')
            cls.config = SOURCES_CFG[cls.CONFIG_ID]
            cls.TOPICS = Topics.with_prefix(cls.config.topic_prefix)


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
        self.heartbeat_interval = 3600

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
            if _is_zero_status(new):
                continue
            if _is_error_report(new):
                json_message = json.dumps(new)
                LOGGER.debug('New error data received from source: %s\ndata:\n%s', name, new)
                await self.client.publish(self.TOPICS.error, json_message)
                last = new
                LOGGER.debug('Wait for new data for %s', self.polling_interval)
                await asyncio.sleep(self.polling_interval)
                continue
            if self.ignore_duplicates and _same_status(new, last):
                if _delta_seconds(new, last) >= self.heartbeat_interval:
                    json_message = json.dumps(new)
                    LOGGER.debug('Duplicate data received from source: %s\ndata:\n%s', name, new)
                    await self.client.publish(self.TOPICS.info, json_message)
                    last = new
                continue
            LOGGER.debug('New data received from source: %s\ndata:\n%s', name, new)
            json_message = json.dumps(new)
            await self.client.publish(self.TOPICS.changes, json_message)
            last = new
            LOGGER.debug('Wait for new data for %s', self.polling_interval)
            await asyncio.sleep(self.polling_interval)


def _delta_seconds(new: dict, last: dict) -> int:
    if last is None:
        return 0
    return new['message_timestamp'] - last['message_timestamp']


def _same_status(new: dict, last: dict) -> bool:
    if last is None:
        return False
    if new == last:
        return True
    this_statuses = {st['name']: st['status'] for st in new['status_list']}
    another_statuses = {st['name']: st['status'] for st in last['status_list']}
    return this_statuses == another_statuses


def _is_error_report(msg: dict) -> bool:
    if 'status_list' in msg:
        for status in msg['status_list']:
            if 'error' in status:
                return True
    return False


def _is_zero_status(msg: dict) -> bool:
    return 'status_list' in msg and not msg['status_list']
