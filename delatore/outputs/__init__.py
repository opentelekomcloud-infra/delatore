"""All delatore outputs"""
import asyncio
import threading

from apubsub import Service

from .alerta import AlertaRunner
from .telegram import BotRunner
from ..configuration import InstanceConfig


async def start_bot(service: Service,
                    stop_event: asyncio.Event,
                    config: InstanceConfig):
    await BotRunner(service, stop_event, config).start()


def start_alerta(service: Service,
                 stop_event: threading.Event,
                 config: InstanceConfig):
    AlertaRunner(service, stop_event, config).start()
