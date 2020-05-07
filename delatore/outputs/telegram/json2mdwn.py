"""Conversion of source data to markdown v2"""
import re

from aiogram.utils.markdown import escape_md, link

from ...outputs.telegram.emoji import EMOJI
from ...unified_json import Status


regex = re.compile(r'([.\-_]{1})')


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
        message = regex.sub(r'\\\1', string)
        status_list = f'Error:\n{message}'
    else:
        if 'status_list' in data:
            status_list = '\n'.join(
                _status_to_md_row(status) for status in data['status_list']
            )
    return f'{src_row}\n{status_list}'


def replace_emoji(status):
    """Replace state of status to emoji"""
    return EMOJI.get(Status(status), '')
