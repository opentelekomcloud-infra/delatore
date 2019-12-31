import logging
from typing import NamedTuple

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

__all__ = ["parse_command"]


def parse_command(message):
    if message.startswith('/status'):
        message = message [len('/status'):]
    return _parse_status(message)


def _parse_status(message):
    LOGGER.debug("Got message: %s", message)
    message = message.replace("\"", "\'")
    print(message)
    arguments = message.split("\'")
    if not arguments:
        return
    arguments[0] = arguments[0].replace(' ', '')
    target: str = arguments[0].split(":")
    name_template = None
    count = 1
    if target[0] == 'awx':
        if len(arguments) > 1:
            name_template = arguments[1].strip()
            if (len(arguments) > 2) & (arguments[2] != ''):
                arguments[2] = arguments[2].replace(" ","")
                count = int(arguments[2])
        else:
            count = None
        LOGGER.debug("Getting AWX status")
    return target[0], name_template, count



