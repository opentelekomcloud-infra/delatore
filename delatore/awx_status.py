import os
import time
from typing import Union, Dict, NamedTuple, List

import requests
#from .emoji import replace_emoji


class Status(NamedTuple):
    timestamp: float
    status: str

    def __str__(self):
        timestamp = time.gmtime(self.timestamp)
        status = "sjdjkl" #replace_emoji(self.status)
        return f"{timestamp} — {status}"



class AwxApiClient:

    def __init__(self):
        self.session = requests.session()
        self.session.headers.update({"Authorization": f"Bearer {os.getenv('AWX_AUTH_TOKEN')}"})
        self.url = 'https://awx.eco.tsi-dev.otc-service.com/api/v2'

    def get_job_templates(self):
        """
        Returns list of all job templates for csm organization

        :return:
        """
        response = self.session.get(url=self.url + '/job_templates')
        return response.json()

    def get_api_endpoints(self):
        """
        Returns list of all awx api endpoints

        :return:
        """
        response = self.session.get(url=self.url)
        return response.json()



    def get_status(self, template: str, count: Union[str, int]) -> List[Dict[str, Dict]]:
        """Get template status from AWX
        :param template: name of template, if empty — all scenarios
        :param count: count of last statuses
        """
        big_d = self.get_job_templates()
        k_value = ['name', 'status', ]
        l = []  # список словарей, описывающий данные одного сценария
        for i in [i for i in big_d['result']]:
            small_dicts = {}
            for k, v in i.items():
                if k in k_value:
                    small_dicts[k].append(v)
            l.append(small_dicts)



    '''
    expected message in telegram:
    You need create function that can parse result of get_job_templates and create message for bot like:
    
    For all scenarios if argument: awx
    For exact scenario if argument: awx:scenario1
    For exact scenario and number of runs if arguments: awx:scenario1, 5
    
    template:
    [❌] (if status = failed)  name | playbook | last_job_run
    [✓] (if status = successful) name | playbook | last_job_run
    [⏳] (if status = never updated) name | playbook | last_job_run
    ...
    
    '''
