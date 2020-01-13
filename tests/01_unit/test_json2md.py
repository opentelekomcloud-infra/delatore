from delatore.emoji import Emoji, replace_emoji
from delatore.json2mdwn import convert


def test_emoji():
    pattern = 'as %a as %e'
    alias_map = {
        'simple': Emoji.RUNNING
    }
    actual = replace_emoji('live is simple', alias_map, pattern)
    expected = f'live is as simple as {Emoji.RUNNING}'
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
