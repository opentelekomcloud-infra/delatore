import re
from typing import NamedTuple


class Emoji(NamedTuple):
    FAILED = '❌'
    RUNNING = '🏃'
    SUCCESS = '✅'
    CANCELED = '⛔'


def replace_emoji(source: str, alias_map: dict):
    """Replace all aliases in text with given emoji

    `alias_map` is just a plain string, not regex
    """
    pattern = re.compile('|'.join(alias_map.keys()))
    text = pattern.sub(lambda p: f'{alias_map[re.escape(p.group(0))]} {p.group(0)}', source)
    return text
