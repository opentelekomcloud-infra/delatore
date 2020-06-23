import asyncio
import logging

from apubsub import Service
from apubsub.client import Client

from . import influx
from .awx_api import AWXApiSource
from .http import AWXWebHookSource
from ..configuration import InstanceConfig

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)


async def start_sources(msg_service: Service, stop_event: asyncio.Event, config: InstanceConfig):
    """Start all sources and make them report to message queue"""
    await asyncio.wait([
        AWXApiSource(msg_service.get_client(), config).start(stop_event),
        AWXWebHookSource(msg_service.get_client()).start(stop_event),
        start_influx_sources(msg_service.get_client(), stop_event, config)
    ])


async def start_influx_sources(msg_service: Client, stop_event: asyncio.Event, config: InstanceConfig):
    await asyncio.wait([
        influx.InfluxSource(msg_service, config).start(stop_event),
        influx.InfluxSourceLBTiming(msg_service, config).start(stop_event),
        influx.InfluxSourceLBDOWN(msg_service, config).start(stop_event),
        influx.InfluxSourceLBDOWNFailCount(msg_service, config).start(stop_event),
        influx.InfluxSourceDiskStateRead(msg_service, config).start(stop_event),
        influx.InfluxSourceDiskStateWrite(msg_service, config).start(stop_event),
        influx.InfluxSourceDiskStateReadSFS(msg_service, config).start(stop_event),
        influx.InfluxSourceDiskStateWriteSFS(msg_service, config).start(stop_event)
    ])
