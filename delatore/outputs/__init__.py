"""All delatore outputs"""
import asyncio
from threading import Event

from apubsub import Service

from .telegram import BotRunner


async def start_outputs(service: Service, stop_event: Event):
    await asyncio.wait([
        BotRunner(service, stop_event).start(),
    ])
