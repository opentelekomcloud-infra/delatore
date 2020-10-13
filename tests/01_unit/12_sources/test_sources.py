import logging

import pytest
from apubsub.client import Client

LOGGER = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_produce_awx_messages(patched_awx_client, sub: Client, pub, awx_client_data):
    data, message = awx_client_data
    LOGGER.debug("Subscribing to AWX changes")
    await sub.subscribe(patched_awx_client.TOPICS.changes)
    LOGGER.debug("Publishing to AWX changes")
    await pub.publish(patched_awx_client._params.topic_in, data[0]['name'])
    LOGGER.debug("Waiting for AWX change message")
    message = await sub.get(.5)
    assert message == message
