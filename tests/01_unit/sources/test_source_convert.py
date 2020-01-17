from delatore.sources import AWXListenerSource, InfluxSource


def test_awx_source(awx_data):
    message, expected = awx_data
    message = AWXListenerSource.convert(message)
    assert message == expected


def test_influx_source(influx_data):
    message, expected = influx_data
    message = InfluxSource.convert(message)
    assert message == expected


def test_convert_template_status(template_status_obj, template_status_msg):
    message = str(template_status_obj)
    assert message == template_status_msg
