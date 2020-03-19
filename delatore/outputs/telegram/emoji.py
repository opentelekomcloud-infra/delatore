import re
from typing import Dict

from ...unified_json import Status

EMOJI = {
    Status.FAIL: '❌',
    Status.RUNNING: '🏃',
    Status.OK: '✅',
    Status.CANCELED: '⛔',
    Status.NO_DATA: '❔',
}


def replace_emoji(source: str, alias_map: Dict[str, str], replacement='%e %a'):
    """Replace all aliases in text with given emoji

    `alias_map` is map of `{"alias": "<emoji>"}`, where "alias" is replaced according to `replacement` schema

    `replacement` has following syntax: `%e` for emoji, `%a` for alias, others characters is treated as plain text
    """
    pattern = re.compile('|'.join(alias_map.keys()))

    def _replace_re(match):
        alias = match.group(0)
        rep_pattern = replacement. \
            replace('%e', alias_map[alias]). \
            replace('%a', alias)
        return rep_pattern

    text = pattern.sub(_replace_re, source)
    return text
