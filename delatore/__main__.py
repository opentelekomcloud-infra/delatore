"""Run bot as python module"""
import asyncio
import os
import threading
from argparse import ArgumentParser
from concurrent import futures

from apubsub import Service


# pylint:disable=import-outside-toplevel

def _config():
    from delatore import configuration as cfg
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
        return cfg.InstanceConfig(token, chat_id, influx_password, awx_auth_token)
    if config_file:
        if not os.path.isfile(config_file):
            raise FileNotFoundError
        return cfg.read_config(config_file)
    raise RuntimeError('Please provide chat ID and bot token or configuration file to use')


async def _ordered_start(service):
    from delatore.outputs import start_bot, start_alerta
    from delatore.sources import start_sources

    config = _config()

    stop_event = asyncio.Event()
    stop_event_thread = threading.Event()
    loop = asyncio.get_running_loop()
    out_bot_task = loop.create_task(start_bot(service,
                                              stop_event,
                                              config))

    await asyncio.sleep(.5)
    src_tsk = loop.create_task(start_sources(service,
                                             stop_event,
                                             config))

    with futures.ThreadPoolExecutor(max_workers=5) as executor:
        executor.submit(start_alerta,
                        service,
                        stop_event_thread,
                        config)

    await asyncio.wait([
        src_tsk,
        out_bot_task,
    ])

    with futures.ThreadPoolExecutor(max_workers=5) as executor:
        executor.submit(start_alerta, service, stop_event_thread, config)


def _main():
    service = Service()
    service.start()

    try:
        asyncio.run(_ordered_start(service))
    finally:
        service.stop()


if __name__ == '__main__':
    _main()
