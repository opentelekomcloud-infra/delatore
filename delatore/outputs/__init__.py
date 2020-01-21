"""All delatore outputs"""
from threading import Event

from apubsub import Service

from .telegram import BotRunner


async def start_outputs(service: Service, stop_event: Event):
    await BotRunner(service, stop_event).start()
