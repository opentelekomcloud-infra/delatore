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
async def patched_awx_client(awx_client_data, service, stop_event, event_loop):
    LOGGER.debug("Creating patched AWX client...")

    async def _get_templates(_, filters: dict = None) -> list:
        LOGGER.debug("Get AWX templates")
        if filters == single_template_filter(''):
            raise KeyError
        return awx_client_data

    client = AWXApiSource(service.get_client(), DEFAULT_INSTANCE_CONFIG)
    client.get_templates = _get_templates
    client.ignore_duplicates = False
    event_loop.create_task(client.start(stop_event))
    yield client
    stop_event.set()
