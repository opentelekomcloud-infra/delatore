"""Configuration loaded from external source"""
import configparser
import os
from typing import NamedTuple, Optional

from ocomone import Resources

RESOURCES = Resources('.', './config')


class InstanceConfig(NamedTuple):
    """Bot configuration container"""
    token: str
    chat_id: str
    influx_password: str
    awx_auth_token: str
    alerta_key: str
    proxy: Optional[str] = None


def read_config(config_file=RESOURCES['config.ini']):
    """Read configuration from configuration file"""
    config = configparser.ConfigParser()
    config.read(config_file)
    defaults = config.defaults()
    if defaults:
        token = defaults.get('token', os.getenv('token'))
        chat_id = defaults.get('chat_id', os.getenv('chat_id'))
        influx_password = defaults.get('influx_password', os.getenv('INFLUX_PASSWORD'))
        awx_auth_token = defaults.get('awx_auth_token', os.getenv('AWX_AUTH_TOKEN'))
        alerta_key = defaults.get('alerta_api_key', os.getenv('ALERTA_API_KEY'))
        proxy = defaults.get('proxy', None)
        return InstanceConfig(token, chat_id, influx_password, awx_auth_token, proxy, alerta_key)
    return InstanceConfig(
        os.getenv('token'),
        os.getenv('chat_id'),
        os.getenv('INFLUX_PASSWORD'),
        os.getenv('AWX_AUTH_TOKEN'),
        os.getenv('ALERTA_API_KEY'),
    )


DEFAULT_INSTANCE_CONFIG = read_config()
