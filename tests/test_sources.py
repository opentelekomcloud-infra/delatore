from delatore.sources.http import AWXSource
from delatore.sources.influx import InfluxSource


def test_awx_source(awx_data):
    message, expected = awx_data
    message = AWXSource.convert(message)
    assert message == expected


def test_influx_source(influx_data):
    message, expected = influx_data
    message = InfluxSource.convert(message)
    assert message == expected
