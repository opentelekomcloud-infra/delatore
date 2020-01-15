import logging
import time
from typing import List, NamedTuple

from aiohttp import ClientSession

from ..configuration import BOT_CONFIG
from ..emoji import Emoji, replace_emoji

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

EMOJI_MAP = {
    'successful': Emoji.SUCCESS,
    'failed': Emoji.FAILED,
    'never updated': Emoji.NO_DATA,
}


class NoSuchTemplate(Exception):
    """Template not found"""


class TemplateStatus(NamedTuple):
    name: str
    last_run_timestamp: str
    last_status: str
    playbook: str

    def __str__(self):
        status = replace_emoji(self.last_status, EMOJI_MAP, '%e')
        timestamp = self.last_run_timestamp
        if timestamp is not None:
            timestamp = time.strftime('%d.%m.%y %H:%M', time.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%fZ'))
        return rf'{status}   —   `{self.name}`  \(`{timestamp}`\)'


def get_session():
    """Get authorized session instance"""
    return ClientSession(headers={'Authorization': f'Bearer {BOT_CONFIG.awx_auth_token}'})


class AWXApiClient:

    def __init__(self):
        self.url = 'https://awx.eco.tsi-dev.otc-service.com/api/v2'

    async def create_status_message(self, template: str = None):
        """Get last job statuses for concrete template or all templates

        :param template: name of template, if empty — all scenarios
        """
        _filter = {'name__iexact': template} if template is not None else None
        try:
            json_data = await self.get_templates(_filter)
        except KeyError:
            raise NoSuchTemplate("No template which has such name")
        except Exception:
            LOGGER.exception("Failed to create status message")
            return
        template_data = get_templates_statuses_from_json(json_data)
        message = '\n'.join(str(i) for i in template_data)
        return message

    async def get_templates(self, filters: dict = None):
        """Returns list of all job templates for csm organization

        This methods support Ansible tower filtering https://docs.ansible.com/ansible-tower/latest/html/towerapi/filtering.html
        """
        async with get_session() as session:
            async with session.get(self.url + '/job_templates', params=filters) as response:
                response_data = await response.json()
            assert response.status == 200, f'Expected response 200, got {response.status}'
        try:
            return response_data['results']
        except KeyError:
            LOGGER.error('No `results` field found in /job_templates response: \nResponse: %s', response_data)
            raise

    async def get_api_endpoints(self):
        """Returns list of all awx api endpoints """
        async with get_session() as session:
            async with session.get(self.url) as response:
                return await response.json()


def get_templates_statuses_from_json(json_data) -> List[TemplateStatus]:
    """Get status for all templates or for concrete template"""
    statuses = []
    for template_data in json_data:
        statuses.append(
            TemplateStatus(name=template_data['name'],
                           last_run_timestamp=template_data['last_job_run'],
                           last_status=template_data['status'],
                           playbook=template_data['playbook']))
    return statuses
