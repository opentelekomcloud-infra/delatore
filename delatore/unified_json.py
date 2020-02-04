import copy
from enum import Enum
from typing import List, Optional

U_TIMESTAMP_FORMAT = '%Y-%m-%dT%H:%M:%S'


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


def convert_timestamp(timestamp: str):
    timestamp, *_ = timestamp.split('.')
    return timestamp
