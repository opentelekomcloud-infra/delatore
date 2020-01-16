import asyncio
from datetime import datetime

import pytest
from apubsub.client import Client

from delatore.sources import AWXApiClient
from delatore.sources.awx_api import TIMESTAMP_FORMAT, TemplateStatus, single_template_filter


def _now():
    return datetime.now().strftime(TIMESTAMP_FORMAT)


S_T_STATUS = TemplateStatus('Scn 3.5', _now(), 'b', 'playbooks/test.yaml')


class MockedAWXClient(AWXApiClient):
    def __init__(self, client):
        super().__init__(client)

    async def get_templates(self, filters: dict = None) -> list:
        if filters == single_template_filter(''):
            raise KeyError
        return [{
            'name': S_T_STATUS.name,
            'last_job_run': S_T_STATUS.last_run_timestamp,
            'status': S_T_STATUS.last_status,
            'playbook': S_T_STATUS.playbook,
        }]


@pytest.fixture
async def awx_client_started(service, stop_event):
    client = MockedAWXClient(service.get_client())
    loop = asyncio.get_running_loop()
    loop.create_task(client.start(stop_event, False))
    yield client
    stop_event.set()


@pytest.mark.asyncio
async def test_produce_messages(awx_client_started, sub: Client, pub):
    await sub.subscribe(awx_client_started.TOPIC)
    await asyncio.sleep(.1)
    await pub.publish(awx_client_started.TOPIC_IN, 'any')
    message = await sub.get(1)
    assert message == f'{S_T_STATUS}'
