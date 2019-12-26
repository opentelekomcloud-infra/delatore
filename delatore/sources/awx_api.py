import logging
import os
from typing import NamedTuple, List

import requests

from delatore import json2mdwn

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)


class TemplateStatus(NamedTuple):
    name: str
    last_run_timestamp: str
    last_status: str
    playbook: str

    def __str__(self):
        return f"name:  {self.name} \n" \
               f"last_run_timestamp:  {self.last_run_timestamp} \n" \
               f"last_run_timestamp:  {self.playbook} \n" \
               f"last_status:  {self.last_status}"


class AwxApiClient:

    def __init__(self):
        self.session = requests.session()
        self.session.headers.update({"Authorization": f"Bearer {os.getenv('AWX_AUTH_TOKEN')}"})
        self.url = 'https://awx.eco.tsi-dev.otc-service.com/api/v2'

    def create_status_message(self, template: str = None):
        """Get last job statuses for concrete template or all templates

        :param template: name of template, if empty — all scenarios
        """
        _filter = {"name__iexact": template}
        json_data = self.get_templates(_filter)
        template_data = get_templates_statuses_from_json(json_data)
        message = json2mdwn.convert(template_data)
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
    list_template_status = []
    for i in json_data:
        list_template_status.append(
            TemplateStatus(name=i['name'], last_run_timestamp=i['last_job_run'], last_status=i['status'],
                           playbook=i['playbook']))
    return list_template_status

