import logging
import shlex
from collections import namedtuple

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

__all__ = ["parse_command"]


class CommandParsingError(Exception):
    """Error during command parsing"""

    def __init__(self, command_name):
        super().__init__(f"Error during {command_name} parsing")


def parse_command(message):
    LOGGER.debug("Got message: %s", message)
    cmd, target, *args = shlex.split(message)
    depth = None
    if ("\'" not in message) and (len(args) > 1):
        raise CommandParsingError(f"Invalid syntax command arguments: {message}")
    detailed = args.pop(0) if args else None
    try:
        depth = int(args.pop(0))
    except IndexError:
        if detailed == None:
            depth = None
        else:
            depth = 1
    except ValueError:
        raise CommandParsingError(f"Invalid depth value: {depth}")
    if args:
     raise CommandParsingError(f"Command {cmd} got unexpected arguments: {args}")
    LOGGER.debug("Getting AWX status")
    return target, detailed, depth

