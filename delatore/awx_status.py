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


""" to be removed """
if __name__ == '__main__':
    client = AwxApiClient()
    result = client.get_job_templates()
    print(result)

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
