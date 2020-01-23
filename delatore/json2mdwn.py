"""Conversion of source data to markdown v2"""

import json
import re


def normalize_key(src: str):
    """Normalize dictionary key format"""
    if src.isupper():
        return f'`{src}`'
    return src.replace('_', ' ').title()


def backtick_values(data):
    """Escape json values with backticks

    To define your behaviour, implement `__md__` method in your class
    """
    if hasattr(data, '__md__'):
        return data.__md__()
    if isinstance(data, dict):
        return {f'{normalize_key(key)} ': backtick_values(data[key]) for key in data}
    if isinstance(data, list):
        return [backtick_values(item) for item in data]
    return f'`{data}`'


__MARKS = re.compile(r'[{}",\[\]]')
__MD2_SPECIAL = re.compile(r'([()])')


def telegram_escape(text):
    """Escape telegram message text"""
    return __MD2_SPECIAL.sub(r'\\\1', text)  # MarkdownV2 chars are escaped


def convert(data):
    """Convert dict or list to nice-looking telegram markdown"""
    formatted = __MARKS.sub('', json.dumps(backtick_values(data),
                                           separators=('', ':    '),
                                           indent=4,
                                           ensure_ascii=False))
    formatted = telegram_escape(formatted)
    formatted = '\n'.join(line[4:].rstrip() for line in formatted.split('\n') if line.rstrip() != '')
    return formatted
