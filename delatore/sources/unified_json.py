import copy
from enum import Enum
from typing import List, Optional

U_TIMESTAMP_FORMAT = '%Y-%m-%dT%H:%M:%S'


class Status(Enum):
    OK = 'OK',
    NO_DATA = 'NO_DATA',
    FAIL = 'FAIL',
    RUNNING = 'RUNNING',
    CANCELED = 'CANCELED',
    SUCCESS = 'SUCCESS',
    NEVER_UPDATED = 'NEVER_UPDATED',


def generate_message(source: str, status_list: List[dict]) -> str:
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
                    timestamp: Optional[float] = None,
                    details_url: Optional[str] = None) -> dict:
    return {
        'name': name,
        'status': status.value,
        'last_timestamp': timestamp,
        'details': details_url
    }
