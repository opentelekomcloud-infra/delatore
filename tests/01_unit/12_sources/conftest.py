import asyncio
import logging
from datetime import datetime

import pytest

from delatore.configuration import DEFAULT_INSTANCE_CONFIG
from delatore.sources import AWXApiSource
from delatore.sources.awx_api import single_template_filter

LOGGER = logging.getLogger(__name__)


def _now():
    return datetime.now()


@pytest.fixture
async def patched_awx_client(awx_client_data, service, stop_event):
    LOGGER.debug("Creating patched AWX client...")

    async def _get_templates(_, filters: dict = None) -> list:
        LOGGER.debug("Get AWX templates")
        if filters == single_template_filter(''):
            raise KeyError
        return awx_client_data

    client = AWXApiSource(service.get_client(), DEFAULT_INSTANCE_CONFIG)
    client.get_templates = _get_templates
    loop = asyncio.get_running_loop()
    client.ignore_duplicates = False
    loop.create_task(client.start(stop_event))
    LOGGER.debug("Started patched AWX client")
    yield client
    LOGGER.debug("Stopping patched AWX client")
    stop_event.set()
