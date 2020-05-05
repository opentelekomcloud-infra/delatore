"""Conversion of source data to markdown v2"""
import re

from aiogram.utils.markdown import escape_md, link

from ...outputs.telegram.emoji import EMOJI
from ...unified_json import Status


def _status_to_md_row(status_record):
    status_emoji = replace_emoji(status_record['status'])
    name = escape_md(status_record['name'])
    timestamp = escape_md(status_record['timestamp'])
    url = status_record['details_url']
    if url:
        timestamp = link(timestamp, url)
    else:
        timestamp = f'`{timestamp or "n/a"}`'
    details = rf'{name} \({timestamp}\)'
    return rf'{status_emoji}  —  {details}'


def convert(data: dict):
    """Convert dict or list to nice-looking telegram markdown"""
    source = escape_md(data['source'])
    src_row = f'*From {source}*'
    status_list = ''
    if 'error' in data['status_list'][0]:
        string = data['status_list'][0]['error']
        substitutions = {".": "\\.", "_": "\\_", "-": "\\-"}
        message = replace(string, substitutions)
        status_list = f'Error:\n{message}'
    else:
        if 'status_list' in data:
            status_list = '\n'.join(
                _status_to_md_row(status) for status in data['status_list']
            )
    return f'{src_row}\n{status_list}'


def replace(string, substitutions):
    """Create regex to replace multiple patterns"""
    substrings = sorted(substitutions, key=len, reverse=True)
    regex = re.compile('|'.join(map(re.escape, substrings)))
    return regex.sub(lambda match: substitutions[match.group(0)], string)


def replace_emoji(status):
    """Replace state of status to emoji"""
    return EMOJI.get(Status(status), '')
