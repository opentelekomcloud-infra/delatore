import copy
import logging
import re
from datetime import datetime
from enum import Enum
from typing import List, Optional

UNIFIED_TIME_PATTERN = '%d.%m.%Y %H:%M:%S'

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


RE_TIME_GROUPS = re.compile(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(\.\d+)?(Z)?')
TIME_PATTERN = '%Y-%m-%dT%H:%M:%S.%fZ'


def convert_timestamp(timestamp: str):
    """Convert timestamp from given format to UNIFIED_TIME_PATTERN"""
    match_ts = RE_TIME_GROUPS.match(timestamp)
    try:
        if match_ts is None:
            raise ValueError
        timestamp, nsec, timezone, *_ = match_ts.groups()
        datetime_object = datetime.strptime(f'{timestamp}{nsec[:6]}{timezone}', TIME_PATTERN)
    except ValueError:
        LOGGER.exception('Failed to convert timestamp: %s', timestamp)
        return ''
    return datetime_object
