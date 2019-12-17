import pytest
import os

from delatore.bot import Delatore
from delatore.sources.influx import Influx


class TestSource:
    def setup(self):
        self.bot = Delatore()

    def test_influx_source(self):
        notifications = Influx(self.bot)
        notifications.connection(host='influx1.eco.tsi-dev.otc-service.com',
                                 username='csm',
                                 password=os.environ['INFLUX_PASSWORD'],
                                 db='csm')

    def test_influx_delete_message(self):
        response = self.bot.delete_message(self.bot.chat_id, self.bot.last_message_id)
        assert response.status_code == 200
