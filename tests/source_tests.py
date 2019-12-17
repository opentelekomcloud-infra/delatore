import pytest
import os

from delatore.bot import Delatore
from delatore.sources.influx import Influx


@pytest.fixture
def create_bot():
    return Delatore()


def test_influx_source(create_bot):
    notifications = Influx(create_bot)
    notifications.connection(host='influx1.eco.tsi-dev.otc-service.com',
                             username='csm',
                             password=os.environ['INFLUX_PASSWORD'],
                             db='csm')


def test_influx_delete_message():
    pass
