import pytest

from delatore.outputs.telegram.json2mdwn import convert

pytestmark = pytest.mark.asyncio


@pytest.mark.asyncio
async def send_and_remove_tg(_bot, text):
    message = await _bot.silent(text)
    await _bot.remove(message.message_id)


def send_and_remove_alerta(_alerta, text):
    message = _alerta.alert(text)
    _alerta.remove(message[1].last_receive_id)


@pytest.mark.asyncio
async def test_send_message_tg(bot):
    await send_and_remove_tg(bot, 'test post to chat')


@pytest.mark.asyncio
async def test_source_message_sending(bot, source_data):
    source, (_, data) = source_data
    message = convert(data)
    await send_and_remove_tg(bot, message)


@pytest.mark.asyncio
async def test_alerta_message_sending(alerta, source_data_alerta):
    source, (_, data) = source_data_alerta
    send_and_remove_alerta(alerta, data)
