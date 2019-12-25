from delatore.bot import CSM_CHAT


def test_send_message(bot):
    response = bot.send_message('test post to chat', CSM_CHAT, disable_notification=True)
    assert bot.last_message_id == response['message_id']


def test_influx_message_sending(bot, influxdb):
    message = influxdb.get_influx_statuses()
    message_converted = influxdb.convert(message)
    response = bot.send_message(message_converted, CSM_CHAT)
    assert bot.last_message_id == response['message_id']
