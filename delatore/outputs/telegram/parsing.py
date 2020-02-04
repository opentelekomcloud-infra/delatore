"""Parsing command arguments """
import logging
import shlex

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

__all__ = ['parse_command', 'CommandParsingError']


class CommandParsingError(Exception):
    """Error during command parsing"""


def parse_command(message):
    """Parsing command arguments to arguments list"""
    LOGGER.debug('Got message: %s', message)
    try:
        cmd, target, *args = shlex.split(message)
    except ValueError:
        raise CommandParsingError('No target provided for `/status` command')
    depth = None
    detailed = args.pop(0) if args else None
    try:
        depth = int(args.pop(0))
    except IndexError:
        depth = 1
    except ValueError:
        raise CommandParsingError(f'Invalid depth value: {depth}')
    if args:
        raise CommandParsingError(f'Command {cmd} got unexpected arguments: {args}')
    return target, detailed, depth
