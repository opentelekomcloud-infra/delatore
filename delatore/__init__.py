import logging

from ocomone import setup_logger

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

setup_logger(LOGGER, 'delatore')
