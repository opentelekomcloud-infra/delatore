import string
from random import choice, randint

import requests

from delatore.bot import Delatore


def random_with_length(length):
    range_start = 10 ** (length - 1)
    range_end = (10 ** length) - 1
    return randint(range_start, range_end)


def random_string(length=10):
    letters = string.ascii_lowercase
    return ''.join(choice(letters) for i in range(length))


class TestMain:
    def setup(self):
        self.bot = Delatore()
        self.session = requests.session()

    def setup_method(self, method):
        self.message = {
            "From": "Ansible Tower",
            "test_job_id": random_with_length(3),
            "test_name": f"Test Send Message {random_string(4)}",
            "status": "failed",
            "test_url": f"https://{random_string()}.{random_string(3)}",
            "test_dict": {
                "test": {
                    "failed": choice([True, False]),
                    "changed": random_with_length(1),
                    "ok": random_with_length(2),
                }
            }
        }

    def teardown_method(self, method):
        response = self.bot.delete_message(self.bot.chat_id, self.bot.last_message_id)
        assert response.status_code == 200

    def test_send_message(self):
        response = self.bot.send_message(self.message, disable_notification=True)
        self.bot.last_message_id = response['result']['message_id']
        assert response["ok"] is True
