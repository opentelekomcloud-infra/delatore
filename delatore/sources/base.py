import asyncio
from abc import ABC, abstractmethod


class SourceField:
    """Descriptor which data to be destroyed after single read"""

    def __init__(self, field: str, converter: str):
        self.field = field
        self.marshaller = converter

    def __get__(self, instance, owner):
        if instance is None:
            return self

        val = None
        if hasattr(instance, self.field):
            val = getattr(instance, self.field)

        setattr(instance, self.field, None)
        return val

    def __set__(self, instance, value):
        if instance is not None:
            value = getattr(instance, self.marshaller)(value)
            setattr(instance, self.field, value)


class Source(ABC):
    """Source API providing base `updates` field"""

    @classmethod
    @abstractmethod
    def convert(cls, data: dict) -> str:
        """Converts json-like object to Telegram supported Markdown

        :param dict data:
        :return: Markdown string
        """
        raise NotImplementedError

    updates = SourceField('__updates__', 'convert')

    @abstractmethod
    async def start(self, stop_event: asyncio.Event):
        """Start consuming"""
