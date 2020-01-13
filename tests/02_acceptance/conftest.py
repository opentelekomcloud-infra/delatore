import pytest

from delatore.bot import bot
from delatore.configuration import CSM_CHAT
from delatore.sources import AWXApiClient, InfluxSource


@pytest.fixture(scope='session')
def awx_client():
    return AWXApiClient()


@pytest.fixture
def cleanup_message():
    yield
    if bot.last_message_id is not None:
        bot.delete_message(CSM_CHAT, bot.last_message_id)


@pytest.fixture(scope='session')
def influxdb():
    return InfluxSource()
