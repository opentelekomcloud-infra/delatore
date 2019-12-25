import logging

from ocomone import setup_logger

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

setup_logger(LOGGER, 'delatore')
