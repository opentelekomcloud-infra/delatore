from delatore.bot import bot
from delatore.configuration import CSM_CHAT


def test_send_message(cleanup_message):
    response = bot.silent(CSM_CHAT, 'test post to chat')
    assert bot.last_message_id == response['message_id']


def test_influx_message_sending(cleanup_message, influxdb):
    message = influxdb.get_influx_statuses()
    message_converted = influxdb.convert(message)
    response = bot.silent(CSM_CHAT, message_converted)
    assert bot.last_message_id == response['message_id']
