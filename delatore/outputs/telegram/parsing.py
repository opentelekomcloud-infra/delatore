"""Parsing command arguments """
import logging
import shlex
from typing import NamedTuple

from attr import dataclass

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

__all__ = ['parse_command', 'CommandParsingError']


class CommandParsingError(Exception):
    """Error during command parsing"""


@dataclass
class ParsedStatusCommand(NamedTuple):
    target: str
    detailed: str = ''
    depth: int = 1

    def __post_init__(self):
        self.depth = int(self.depth)


def parse_command(message) -> ParsedStatusCommand:
    """Parsing command arguments to arguments list"""
    LOGGER.debug('Got message: %s', message)
    try:
        _, target, *args = shlex.split(message)
    except ValueError:
        raise CommandParsingError('Issues provided by `/status` command')
    return ParsedStatusCommand(target, *args)
