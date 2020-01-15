"""All delatore outputs"""
import asyncio
from asyncio import Event

from apubsub import Service

from .telegram import start_bot


async def start_outputs(service: Service, stop_event: Event):
    await asyncio.wait([
        start_bot(service, stop_event),
    ])
