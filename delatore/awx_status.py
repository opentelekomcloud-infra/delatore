import os

import requests


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


    def f(self, argument):
             k_value = ('status', 'name', ' playbook', 'last_job_run')
             if __name__ == '__main__':
                 self.client = AwxApiClient()
                 big_d = self.client.get_job_templates()
             """
             big_d - большой словарь
             k_value - список значений трех ключей
             находим по ключу result внутренний большой список big_d['results']
             """
             l = []
             for i in [i for i in big_d['results']]:
                 small_dicts = {}
                 for k, v in i.items():
                     if k in k_value:
                         small_dicts[k].append(v)
                 l.append(small_dicts)
             return l


""" to be removed """


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
