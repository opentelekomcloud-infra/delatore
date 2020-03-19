"""All delatore outputs"""
import asyncio
from threading import Event

from apubsub import Service

from .alerta import AlertaRunner
from .telegram import BotRunner
from ..configuration import InstanceConfig


async def start_outputs(service: Service, stop_event: Event, config: InstanceConfig):
    await asyncio.wait([
        AlertaRunner(service, stop_event, config).start(),
        BotRunner(service, stop_event, config).start(),
    ])
