"""Some helper functions"""
import logging

import wrapt

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)


# noinspection PyBroadException
@wrapt.decorator
def log_errors(wrapped, _=None, args=(), kwargs=None):
    try:
        return wrapped(*args, **kwargs)
    except Exception:
        LOGGER.exception('Unhandled exception')
