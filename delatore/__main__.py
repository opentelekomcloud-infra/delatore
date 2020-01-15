"""Run bot as python module"""
import os
from argparse import ArgumentParser

from aiogram import executor

from delatore import configuration as cfg


def _config():
    arg_p = ArgumentParser(description='Bot for reporting CSM monitoring status to telegram channel')
    arg_p.add_argument('--config', default=None, help='Configuration file to use')
    arg_p.add_argument('--chat', default=os.getenv('chat_id'), help='Chat for notifications')
    arg_p.add_argument('--token', default=os.getenv('token'), help='Telegram bot token')
    arg_p.add_argument('--influx_password', default=os.getenv('INFLUX_PASSWORD'), help='Influx password')
    arg_p.add_argument('--awx_auth_token', default=os.getenv('AWX_AUTH_TOKEN'), help='OAuth2 Token for Ansible Tower')

    args = arg_p.parse_args()
    config_file = args.config
    token, chat_id, influx_password, awx_auth_token = args.token, args.chat, args.influx_password, args.awx_auth_token

    if all([token, chat_id, influx_password, awx_auth_token]):
        cfg.BOT_CONFIG = cfg.BotConfig(token, chat_id, influx_password, awx_auth_token)
    elif config_file:
        if not os.path.isfile(config_file):
            raise FileNotFoundError
        cfg.BOT_CONFIG = cfg.read_config(config_file)
    else:
        raise RuntimeError('Please provide chat ID and bot token or configuration file to use')


def _main():
    _config()
    from delatore.bot import DISP
    executor.start_polling(DISP)


_main()
