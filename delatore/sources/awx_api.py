import asyncio
import logging
import time
from typing import List, NamedTuple, Optional, Dict

from aiohttp import ClientSession
from apubsub.client import Client

from .base import NoUpdates, Source
from .unified_json import Status, generate_status, generate_message
from ..configuration import BOT_CONFIG

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)


def switch_status(argument) -> Status:
    status = {
        'successful': Status.SUCCESS,
        'failed': Status.FAIL,
        'never updated': Status.NEVER_UPDATED
    }
    return status.get(argument, 'Invalid status')


TIMESTAMP_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'

NO_TEMPLATE_PATTERN = 'No template with name \'{}\' found'  # pylint:disable=invalid-string-quote


def get_session():
    """Get authorized session instance"""
    return ClientSession(headers={'Authorization': f'Bearer {BOT_CONFIG.awx_auth_token}'})


class AWXParams(NamedTuple):
    """Influx params storage"""
    host: str
    topic_in: str


class AWXApiSource(Source):
    """AWX API Client"""

    CONFIG_ID = 'awx_api'
    _params: Optional[AWXParams] = None

    async def get_update(self):
        template_name = await self.client.get(self.polling_interval)
        if template_name is None:
            raise NoUpdates

        _filter = single_template_filter(template_name)
        data = await self.get_templates(_filter) or [NO_TEMPLATE_PATTERN.format(template_name)]
        return data

    @classmethod
    def convert(cls, data: List[Dict]) -> Dict:
        return generate_message(cls.CONFIG_ID, data)

    @classmethod
    def params(cls) -> AWXParams:
        if cls._params is None:
            cls._params = AWXParams(**cls.config.params)
        return cls._params

    def __init__(self, client: Client):
        # polling here - polling of input requests
        # request timeout - timeout for API request
        super().__init__(client, ignore_duplicates=False)

    async def start(self, stop_event: asyncio.Event):
        await self.client.start_consuming()
        await self.client.subscribe(self.params().topic_in)
        await super().start(stop_event)

    async def get_templates(self, filters: dict = None) -> Optional[list]:
        """Returns list of all job templates for csm organization

        This methods support Ansible tower filtering
        https://docs.ansible.com/ansible-tower/latest/html/towerapi/filtering.html
        """
        async with get_session() as session:
            async with session.get(self.params().host + '/job_templates', params=filters, timeout=5) as response:
                response_data = await response.json()
            assert response.status == 200, f'Expected response 200, got {response.status}'
        try:
            return _status_json(response_data['results'])
        except KeyError:
            LOGGER.error('No `results` field found in /job_templates response: \nResponse: %s', response_data)
            raise


def single_template_filter(template_name: str):
    """Filter by exact template name"""
    if template_name:
        return {'name__iexact': template_name}
    return None


def _status_json(json_data) -> List[Dict]:
    """Get status for all templates or for concrete template"""
    data = []
    for template_data in json_data:
        data.append(
            generate_status(name=template_data['name'],
                            status=template_data['status'],
                            timestamp=convert_last_run_time(template_data['last_job_run']),
                            )
        )
    return data


def convert_last_run_time(last_run_timestamp: str):
    timestamp = last_run_timestamp
    if timestamp is not None:
        timestamp = time.strftime('%d.%m.%y %H:%M', time.strptime(timestamp, TIMESTAMP_FORMAT))
    return timestamp
# TODO: try catch
