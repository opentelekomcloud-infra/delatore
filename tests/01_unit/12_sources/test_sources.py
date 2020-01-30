import pytest
from apubsub.client import Client


@pytest.mark.asyncio
async def test_produce_awx_messages(patched_awx_client, sub: Client, pub, service, awx_client_data):
    data, message = awx_client_data
    await sub.subscribe(patched_awx_client.TOPIC)
    await pub.publish(patched_awx_client.params().topic_in, data[0]['name'])
    message = await sub.get(.5)
    assert message == message
