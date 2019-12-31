import pytest

from delatore.bot.parsing import parse_command


@pytest.mark.parametrize(['quo'], "\'\"")
def test_parse_quotted_message(quo):
    expected = ('awx', 'Scenario 1.5', 5)
    message = f'{expected[0]}:\'{expected[1]}\'{expected[2]}'
    source, detailed, count = parse_command(message)
    assert (source, detailed, count) == expected


@pytest.mark.parametrize(('message', 'expected'),
                         [
                             ('/status awx:\'Destroy\' 1', ('awx', 'Destroy', 1)),
                             ('/status awx:"scenario 1"', ('awx', 'scenario 1',1)),
                             ('/status awx', ('awx', None, None)),
                         ])
def test_parse_command(message, expected):
    source, detailed, count = parse_command(message)
    assert (source, detailed, count) == expected
