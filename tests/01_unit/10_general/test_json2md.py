from delatore.outputs.telegram.emoji import EMOJI, replace_emoji
from delatore.unified_json import Status, convert_timestamp


def test_emoji():
    pattern = 'as %a as %e'
    alias_map = {
        'simple': EMOJI[Status.RUNNING]
    }
    actual = replace_emoji('live is simple', alias_map, pattern)
    expected = f'live is as simple as {EMOJI[Status.RUNNING]}'
    assert actual == expected


def test_json2mdwn(json2mdwn_data):
    actual, expected = json2mdwn_data
    assert actual == expected


def test_time_convert(time_data):
    actual_date, received_date, TIME_PATTERN = time_data
    converted_date = convert_timestamp(received_date, TIME_PATTERN)
    assert converted_date != ''
    assert converted_date == actual_date
