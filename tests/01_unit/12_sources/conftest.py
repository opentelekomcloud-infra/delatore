import asyncio
from datetime import datetime

import pytest

from delatore.configuration import DEFAULT_INSTANCE_CONFIG
from delatore.sources import AWXApiSource
from delatore.sources.awx_api import single_template_filter


def _now():
    return datetime.now()


@pytest.fixture
async def patched_awx_client(awx_client_data, service, stop_event):
    async def _get_templates(_, filters: dict = None) -> list:
        if filters == single_template_filter(''):
            raise KeyError
        return awx_client_data

    client = AWXApiSource(service.get_client(), DEFAULT_INSTANCE_CONFIG)
    client.get_templates = _get_templates
    loop = asyncio.get_running_loop()
    client.ignore_duplicates = False
    loop.create_task(client.start(stop_event))
    yield client
    stop_event.set()

# @pytest.fixture
# async def alerta_client(awx_client_data, service, threading_stop_event):
#     alerta = AlertaRunner(service, threading_stop_event, DEFAULT_INSTANCE_CONFIG)
#     await alerta.start()
#     yield alerta
#     threading_stop_event.set()
