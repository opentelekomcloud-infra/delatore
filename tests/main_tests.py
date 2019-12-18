import string
from random import choice, randint


def random_with_length(length):
    range_start = 10 ** (length - 1)
    range_end = (10 ** length) - 1
    return randint(range_start, range_end)


def random_string(length=10):
    letters = string.ascii_lowercase
    return ''.join(choice(letters) for i in range(length))


def test_send_message(bot):
    response = bot.send_message("test post to chat", disable_notification=True)
    bot.last_message_id = response['result']['message_id']
    assert response["ok"] is True
