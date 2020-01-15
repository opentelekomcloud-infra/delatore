import pytest


@pytest.mark.asyncio
async def test_influx_data(influxdb):
    await influxdb.get_influx_statuses()
