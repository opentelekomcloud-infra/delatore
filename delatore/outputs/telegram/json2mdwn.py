"""Conversion of source data to markdown v2"""
from aiogram.utils.markdown import escape_md, link

from delatore.outputs.telegram.emoji import EMOJI
from delatore.unified_json import Status


def normalize_key(src: str):
    """Normalize dictionary key format"""
    src = escape_md(src)
    if src.isupper():
        return f'`{src}`'
    return src.replace('_', ' ').title()


def _status_to_md_row(status_record):
    status_emoji = replace_emoji(status_record['status'])
    name = escape_md(status_record['name'])
    timestamp = escape_md(status_record['timestamp'])
    url = status_record['details_url']
    details_url = link(rf'{name} \({timestamp}\)', url) if url else name
    return rf'{status_emoji}  —  {details_url}'


def convert(data: dict):
    """Convert dict or list to nice-looking telegram markdown"""
    source = escape_md(data['source'])
    src_row = f'*From {source}*'
    if 'status_list' in data:
        status_list = '\n'.join(
            _status_to_md_row(status) for status in data['status_list']
        )
    else:
        status_list = data['error']
    # `status_emoji` — [Scenario 1  \(12.12.1991 00:12\)](https://awx...)
    return f'{src_row}\n{status_list}'


def replace_emoji(status):
    return EMOJI[switch_status(status)]


def switch_status(argument: str):
    status = {
        'ok': Status.OK,
        'fail': Status.FAIL,
        'no_data': Status.NO_DATA,
        'running': Status.RUNNING,
        'success': Status.OK,
        'failed': Status.FAIL,
        'canceled': Status.FAIL,
    }
    return status.get(argument, 'Invalid status')
