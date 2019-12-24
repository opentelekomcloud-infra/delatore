from delatore.bot import CSM_CHAT
from delatore.sources.influx import InfluxSource


def test_send_message(bot):
    response = bot.send_message('test post to chat', CSM_CHAT, disable_notification=True)
    assert bot.last_message_id == response['message_id']


def test_influx_message_sending(bot):
    source = InfluxSource()
    message = source.connection()
    message_converted = source.convert(message)
    bot.send_message(message_converted, CSM_CHAT)
