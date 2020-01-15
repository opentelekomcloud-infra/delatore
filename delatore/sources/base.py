import asyncio
from abc import ABC, abstractmethod
from typing import Optional, Union

from apubsub.client import Client

Json = Union[dict, list]


class NoUpdates(Exception):
    """Raised when source has no updates"""


class Source(ABC):
    """Source API posting updates to """

    client: Client
    TOPIC: str

    def __init__(self, client: Client, polling_interval=10.0):
        self.client = client
        self.polling_interval = polling_interval
        if not hasattr(self, 'TOPIC'):
            raise NotImplementedError(f'Source has no topic')

    @abstractmethod
    async def get_update(self) -> Optional[Json]:
        """Get source update"""""

    @classmethod
    @abstractmethod
    def convert(cls, data: Json) -> str:
        """Converts json-like object to Telegram supported Markdown

        :param data: JSON dictionary or list
        :return: Markdown string
        """

    async def start(self, stop_event: asyncio.Event, no_duplicates=True):
        """Start consuming"""
        last = None
        while not stop_event.is_set():
            try:
                new = await self.get_update()
            except NoUpdates:
                await asyncio.sleep(self.polling_interval)
                continue
            if (new is None) or ((new == last) and no_duplicates):
                await asyncio.sleep(self.polling_interval)
                continue
            md_message = self.convert(new)
            self.client.publish(self.TOPIC, md_message)
            last = new
            await asyncio.sleep(self.polling_interval)
