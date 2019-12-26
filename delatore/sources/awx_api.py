import logging
import os
import time
from typing import NamedTuple, List

import requests

from ..emoji import replace_emoji, Emoji

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

EMOJI_MAP = {
    'successful': Emoji.SUCCESS,
    'failed': Emoji.FAILED,
    'never updated': Emoji.NO_DATA,
}


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
        return f'{status}   —   `{self.name}`  (`{timestamp}`)'


class AwxApiClient:

    def __init__(self):
        self.session = requests.session()
        self.session.headers.update({'Authorization': f'Bearer {os.getenv("AWX_AUTH_TOKEN")}'})
        self.url = 'https://awx.eco.tsi-dev.otc-service.com/api/v2'

    def create_status_message(self, template: str = None):
        """Get last job statuses for concrete template or all templates

        :param template: name of template, if empty — all scenarios
        """
        _filter = {'name__iexact': template}
        json_data = self.get_templates(_filter)
        template_data = get_templates_statuses_from_json(json_data)
        message = '\n'.join(str(i) for i in template_data)
        return message

    def get_templates(self, filters: dict = None):
        """Returns list of all job templates for csm organization

        This methods support ansible tower filtering https://docs.ansible.com/ansible-tower/latest/html/towerapi/filtering.html
        """
        response = self.session.get(url=self.url + '/job_templates', params=filters)
        assert response.status_code == 200, f'Expected response 200, got {response.status_code} ({response.text})'
        response_data = response.json()
        try:
            return response_data['results']
        except KeyError:
            LOGGER.error('No `results` field found in /job_templates response: \nResponse: %s', response_data)
            raise

    def get_api_endpoints(self):
        """Returns list of all awx api endpoints """
        response = self.session.get(url=self.url)
        return response.json()


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
