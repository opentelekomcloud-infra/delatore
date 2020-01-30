from delatore.outputs.telegram.emoji import EMOJI, replace_emoji
from delatore.outputs.telegram.json2mdwn import convert
from delatore.unified_json import Status


def test_emoji():
    pattern = 'as %a as %e'
    alias_map = {
        'simple': EMOJI[Status.RUNNING]
    }
    actual = replace_emoji('live is simple', alias_map, pattern)
    expected = f'live is as simple as {EMOJI[Status.RUNNING]}'
    assert actual == expected


def test_backtick():
    data = {
        'item': 'value',
        'list': [
            'a',
            'b'
        ],
        'dict': {
            'item': 'value'
        }
    }
    expected = ('Item :    `value`\n'
                'List :\n'
                '    `a`\n'
                '    `b`\n'
                'Dict :\n'
                '    Item :    `value`')
    assert convert(data) == expected
