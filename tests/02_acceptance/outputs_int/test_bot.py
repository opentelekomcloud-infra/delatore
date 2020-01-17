import pytest

from delatore.sources import AWXApiClient, AWXListenerSource, InfluxSource
from delatore.sources.base import Json, Source
from tests.helpers import random_awx_data, random_influx_data, random_template_data


async def send_and_remove(_bot, text):
    message = await _bot.silent(text)
    await _bot.remove(message.message_id)


@pytest.mark.asyncio
async def test_send_message(bot):
    await send_and_remove(bot, 'test post to chat')


@pytest.mark.parametrize(('source', 'data'), [
    (InfluxSource, random_influx_data()),
    (AWXListenerSource, random_template_data()),
    (AWXApiClient, random_awx_data())
])
@pytest.mark.asyncio
async def test_source_message_sending(bot, source: Source, data: Json):
    message_converted = source.convert(data)
    await send_and_remove(bot, message_converted)
