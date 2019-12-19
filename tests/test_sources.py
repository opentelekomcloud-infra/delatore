from delatore.sources.http import AWXSource


def test_awx_source(awx_data):
    message, expected = awx_data
    message = AWXSource.convert(message)
    assert message == expected
