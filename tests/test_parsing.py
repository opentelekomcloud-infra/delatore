import pytest

from delatore.bot.parsing import parse_command, CommandParsingError


@pytest.mark.parametrize(['quo'], "\'\"")
def test_parse_quotted_message(quo):
    expected = ('awx', 'Scenario 1.5', 5)
    message = f'/status {expected[0]} \'{expected[1]}\' {expected[2]}'
    source, detailed, count = parse_command(message)
    assert (source, detailed, count) == expected


@pytest.mark.parametrize(('message', 'expected'),
                         [
                             ('/status awx \'Scenario 1.5\' 5', ('awx', 'Scenario 1.5', 5)),
                             ('/status awx', ('awx', None, None)),
                             ('/status awx \'Destroy 1\' ', ('awx', 'Destroy 1', 1))
                         ])
def test_parse_command(message, expected):
    source, detailed, count = parse_command(message)
    assert (source, detailed, count) == expected

def test_parse_err(message = '/status awx Destroy test host 5'):
    with pytest.raises(CommandParsingError):
        source, detailed, count = parse_command(message)
