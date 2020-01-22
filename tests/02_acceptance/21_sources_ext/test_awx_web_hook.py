import asyncio

import pytest
from aiohttp import ClientSession
from apubsub.client import Client

from delatore.sources import AWXWebHookSource

pytestmark = pytest.mark.asyncio


async def test_http_server_listening(awx_web_hook_src: AWXWebHookSource):
    async with ClientSession() as session:
        async with session.get(f'http://localhost:{awx_web_hook_src.port}/',
                               timeout=5) as response:
            data = await response.text()
    assert response.status == 200
    assert data == 'OK'


async def test_http_server_notification(awx_web_hook_src: AWXWebHookSource, sub: Client, awx_hook_data):
    await sub.subscribe(awx_web_hook_src.TOPIC)
    await asyncio.sleep(.1)
    job_metadata, expected_str = awx_hook_data
    async with ClientSession() as session:
        async with session.post(f'http://localhost:{awx_web_hook_src.port}/notifications',
                                json=job_metadata, timeout=5) as resp:
            pass
    assert resp.status == 200
    data = await sub.get(.5)
    assert data == expected_str
