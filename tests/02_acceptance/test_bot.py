import asyncio

from delatore.bot import silent
from delatore.configuration import CSM_CHAT


def test_send_message():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(silent(CSM_CHAT, 'test post to chat'))
