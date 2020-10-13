"""Parsing command arguments """
import logging
import shlex
from dataclasses import dataclass

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

__all__ = ['parse_command', 'CommandParsingError']


class CommandParsingError(Exception):
    """Error during command parsing"""


@dataclass
class ParsedStatusCommand:
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
        return ParsedStatusCommand(target, *args)
    except ValueError as ex:
        raise CommandParsingError('Incorrect `/status` command') from ex
    except TypeError as ex:
        raise CommandParsingError('Too many arguments for `/status` command') from ex
