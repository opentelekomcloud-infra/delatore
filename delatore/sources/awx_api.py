import asyncio
import logging
from typing import Dict, List, NamedTuple, Optional

from aiohttp import ClientSession
from apubsub.client import Client

from .base import NoUpdates, Source
from ..configuration import InstanceConfig
from ..unified_json import Status, convert_timestamp, generate_error, generate_message, generate_status

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

__awx_status_override = {
    'failed': Status.FAIL,
    'successful': Status.OK,
    'canceled': Status.CANCELED
}


def switch_awx_status(argument) -> Status:
    status = __awx_status_override.get(argument, argument)
    return Status(status)


NO_TEMPLATE_PATTERN = 'No template with name \'{}\' found'  # pylint:disable=invalid-string-quote
AWX_API_TIME_PATTERN = '%Y-%m-%dT%H:%M:%S.%fZ'


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
        data = await self.get_templates(_filter)
        data = self.convert(data, template_name)
        return data

    @classmethod
    def convert(cls, data: List[Dict], template_name) -> Dict:
        if not data:
            return generate_error(cls.CONFIG_ID, NO_TEMPLATE_PATTERN.format(template_name))
        status_list = []
        for record in data:
            status_list.append(
                generate_status(
                    name=record['name'],
                    status=switch_awx_status(record['status']),
                    timestamp=convert_timestamp(record['last_job_run'], AWX_API_TIME_PATTERN),
                )
            )
        return generate_message(cls.CONFIG_ID, status_list)

    @classmethod
    def params(cls) -> AWXParams:
        if cls._params is None:
            cls._params = AWXParams(**cls.config.params)
        return cls._params

    def __init__(self, client: Client, instance_config: InstanceConfig):
        # polling here - polling of input requests
        # request timeout - timeout for API request
        super().__init__(client, ignore_duplicates=False)
        self.instance_config = instance_config

    def get_session(self):
        """Get authorized session instance"""
        return ClientSession(headers={'Authorization': f'Bearer {self.instance_config.awx_auth_token}'})

    async def start(self, stop_event: asyncio.Event):
        await self.client.start_consuming()
        await self.client.subscribe(self.params().topic_in)
        await super().start(stop_event)

    async def get_templates(self, filters: dict = None) -> Optional[list]:
        """Returns list of all job templates for csm organization

        This methods support Ansible tower filtering
        https://docs.ansible.com/ansible-tower/latest/html/towerapi/filtering.html
        """
        async with self.get_session() as session:
            async with session.get(self.params().host + '/job_templates', params=filters, timeout=5) as response:
                response_data = await response.json()
            assert response.status == 200, f'Expected response 200, got {response.status}'
        try:
            return response_data['results']
        except KeyError:
            LOGGER.error('No `results` field found in /job_templates response: \nResponse: %s', response_data)
            raise


def single_template_filter(template_name: str):
    """Filter by exact template name"""
    if template_name:
        return {'name__iexact': template_name}
    return None
