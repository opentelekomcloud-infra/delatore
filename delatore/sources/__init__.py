import asyncio
import logging

from apubsub import Service

from .awx_api import AWXApiSource
from .http import AWXWebHookSource
from .influx import InfluxSource

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)


async def start_sources(msg_service: Service, stop_event: asyncio.Event):
    """Start all sources and make them report to message queue"""
    await asyncio.wait([
        AWXApiSource(msg_service.get_client()).start(stop_event),
        AWXWebHookSource(msg_service.get_client()).start(stop_event),
        InfluxSource(msg_service.get_client()).start(stop_event),
    ])
