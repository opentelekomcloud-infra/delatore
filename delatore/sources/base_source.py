from abc import ABC


class Source(ABC):
    """Source API providing base `updates` field"""

    @property
    def updates(self) -> dict:
        """Last data received from source"""
        raise NotImplementedError
