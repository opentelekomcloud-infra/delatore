import asyncio
import logging
import time
from typing import List, NamedTuple, Optional

from aiohttp import ClientSession
from apubsub.client import Client

from .base import NoUpdates, Source
from ..configuration import BOT_CONFIG
from ..emoji import Emoji, replace_emoji
from ..json2mdwn import convert

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

AWX_EMOJI_MAP = {
    'successful': Emoji.SUCCESS,
    'failed': Emoji.FAILED,
    'never updated': Emoji.NO_DATA,
}

TIMESTAMP_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'

NO_TEMPLATE_PATTERN = 'No template with name \'{}\' found'  # pylint:disable=invalid-string-quote


class TemplateStatus(NamedTuple):
    name: str
    last_run_timestamp: str
    last_status: str
    playbook: str

    def __md__(self):
        status = replace_emoji(self.last_status, AWX_EMOJI_MAP, '%e')
        timestamp = self.last_run_timestamp
        if timestamp is not None:
            timestamp = time.strftime('%d.%m.%y %H:%M', time.strptime(timestamp, TIMESTAMP_FORMAT))
        return rf'{status}   —   `{self.name}`  (`{timestamp}`)'


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
    def convert(cls, data: list) -> str:
        return f'* AWX scenarios status: *\n{convert(data)}'

    @classmethod
    def params(cls) -> AWXParams:
        if cls._params is None:
            cls._params = AWXParams(**cls.config.params)
        return cls._params

    def __init__(self, client: Client):
        # polling here - polling of input requests
        # request timeout - timeout for API request
        super().__init__(client,
                         polling_interval=.1,  # polling for command inputs
                         request_timeout=10,
                         ignore_duplicates=False)

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


def _status_json(json_data) -> List[TemplateStatus]:
    """Get status for all templates or for concrete template"""
    statuses = []
    for template_data in json_data:
        statuses.append(
            TemplateStatus(name=template_data['name'],
                           last_run_timestamp=template_data['last_job_run'],
                           last_status=template_data['status'],
                           playbook=template_data['playbook']))
    return statuses
