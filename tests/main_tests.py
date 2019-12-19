def test_send_message(bot):
    response = bot.send_message('test post to chat', disable_notification=True)
    bot.last_message_id = response['result']['message_id']
    assert response['ok'] is True
