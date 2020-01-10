"""Run bot as python module"""
import os
from argparse import ArgumentParser

from delatore import configuration


def _config():
    arg_p = ArgumentParser(description="Bot for reporting CSM monitoring status to telegram channel")
    arg_p.add_argument("--config", default=None, help="Configuration file to use")
    arg_p.add_argument("--chat", default=os.getenv("chat_id"), help="Chat for notifications")
    arg_p.add_argument("--token", default=os.getenv("token"), help="Telegram bot token")
    arg_p.add_argument("--influx_password", default=os.getenv("INFLUX_PASSWORD"), help="Influx password")
    arg_p.add_argument("--awx_auth_token", default=os.getenv("AWX_AUTH_TOKEN"), help="OAuth2 Token for Ansible Tower")
    args = arg_p.parse_args()
    config_file = args.config
    token, chat_id, influx_password = args.token, args.chat, args.influx_password
    if all([token, chat_id, influx_password]):
        configuration.BOT_CONFIG = configuration.BotConfig(args.token, args.chat, args.influx_password, args.AWX_AUTH_TOKEN)
    elif config_file:
        if not os.path.isfile(config_file):
            raise FileNotFoundError
        configuration.BOT_CONFIG = configuration.read_config(config_file)
    else:
        raise RuntimeError("Please provide chat ID and bot token or configuration file to use")


def _main():
    _config()
    from delatore.bot import bot
    bot.start()


_main()
