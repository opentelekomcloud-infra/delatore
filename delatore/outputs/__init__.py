"""All delatore outputs"""
from threading import Event

from apubsub import Service

from .telegram import BotRunner
from ..configuration import InstanceConfig


async def start_outputs(service: Service, stop_event: Event, config: InstanceConfig):
    await BotRunner(service, stop_event, config).start()
