from delatore.bot import CSM_CHAT


def test_send_message(bot):
    response = bot.send_message('test post to chat', CSM_CHAT, disable_notification=True)
    assert bot.last_message_id == response['message_id']
