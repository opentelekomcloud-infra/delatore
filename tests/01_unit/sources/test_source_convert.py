def test_convert(source_data):
    source, (data, expected) = source_data
    converted = source.convert(data)
    assert converted == expected
