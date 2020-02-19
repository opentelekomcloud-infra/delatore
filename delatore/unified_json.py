import copy
import logging
from datetime import datetime
from enum import Enum
from typing import List, Optional

UNIFIED_TIME_PATTERN = '%d.%m.%Y %H:%M'

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)


class Status(Enum):
    """Possible task statuses"""
    OK = 'ok'
    NO_DATA = 'no_data'
    FAIL = 'fail'
    RUNNING = 'running'
    CANCELED = 'canceled'

    _INVALID = 'invalid status'

    @classmethod
    def _missing_(cls, _):
        return cls._INVALID


def generate_message(source: str, status_list: List[dict]) -> dict:
    """Generate status message"""
    return {
        'source': source,
        'status_list': copy.deepcopy(status_list),
    }


def generate_error(source: str, message: str) -> dict:
    """Generate error message"""
    return {
        'source': source,
        'error': message,
    }


def generate_status(name: str,
                    status: Status,
                    timestamp: Optional[str] = None,
                    details_url: Optional[str] = None) -> dict:
    """Generate single status line"""
    return {
        'name': name,
        'status': status.value,
        'timestamp': timestamp,
        'details_url': details_url
    }


def convert_timestamp(timestamp: str, timestamp_fmt: str) -> str:
    """Convert timestamp from given format to UNIFIED_TIME_PATTERN"""
    try:
        datetime_object = datetime.strptime(timestamp, timestamp_fmt)
    except ValueError:
        LOGGER.exception('Failed to convert timestamp: %s', timestamp)
        return ''
    return datetime_object.strftime(UNIFIED_TIME_PATTERN)
