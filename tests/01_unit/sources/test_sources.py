import pytest
from apubsub.client import Client


@pytest.mark.asyncio
async def test_produce_messages(patched_awx_client, sub: Client, pub, template_status_obj, service):
    await sub.subscribe(patched_awx_client.TOPIC)
    await pub.publish(patched_awx_client.TOPIC_IN, 'any')
    message = await sub.get(.5)
    assert message == str(template_status_obj)
