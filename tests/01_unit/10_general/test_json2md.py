from delatore.outputs.telegram.emoji import EMOJI, replace_emoji
from delatore.unified_json import Status


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
