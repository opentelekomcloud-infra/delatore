import copy
import logging
from datetime import datetime
from enum import Enum
from typing import List, Optional

U_TIMESTAMP_FORMAT = '%Y-%m-%dT%H:%M:%S'
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)


class Status(Enum):
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
    return {
        'source': source,
        'status_list': copy.deepcopy(status_list),
    }


def generate_error(source: str, message: str) -> dict:
    return {
        'source': source,
        'error': message,
    }


def generate_status(name: str,
                    status: Status,
                    timestamp: Optional[str] = None,
                    details_url: Optional[str] = None) -> dict:
    return {
        'name': name,
        'status': status.value,
        'timestamp': convert_timestamp(timestamp),
        'details_url': details_url
    }


UNIFIED_TIME_PATTERN = '%d.%m.%Y %H:%M'


def convert_timestamp(timestamp: str) -> str:
    timestamp, *_ = timestamp.split('.')
    try:
        datetime_object = datetime.strptime(timestamp, U_TIMESTAMP_FORMAT)
    except ValueError:
        LOGGER.exception('Failed to convert timestamp: %s', timestamp)
        return ''
    return datetime_object.strftime(UNIFIED_TIME_PATTERN)
