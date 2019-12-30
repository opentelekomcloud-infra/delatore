import configparser
import os
from typing import NamedTuple

from ocomone import Resources

RESOURCES = Resources('.', '../config')

TG_URL = 'https://api.telegram.org/bot'


class BotConfig(NamedTuple):
    """Bot configuration container"""
    token: str
    chat_id: str

    @property
    def url(self):
        return f'{TG_URL}{self.token}/'


def read_config(config_file=RESOURCES['config.ini']):
    """Read configuration from configuration file"""
    config = configparser.ConfigParser()
    config.read(config_file)
    defaults = config.defaults()
    if defaults:
        token = defaults.get('token', os.getenv('token'))
        chat_id = defaults.get('chat_id', os.getenv('chat_id'))
        return BotConfig(token, chat_id)
    return BotConfig(
        os.getenv('token'),
        os.getenv('chat_id'),
    )


BOT_CONFIG = read_config()

CSM_CHAT = BOT_CONFIG.chat_id
