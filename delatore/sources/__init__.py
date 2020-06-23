import asyncio
import logging

from apubsub import Service
from apubsub.client import Client

from .awx_api import AWXApiSource
from .http import AWXWebHookSource
from .influx import (InfluxSource, InfluxSourceDiskStateRead, InfluxSourceDiskStateReadSFS, InfluxSourceDiskStateWrite,
                     InfluxSourceDiskStateWriteSFS, InfluxSourceLBDOWN, InfluxSourceLBDOWNFailCount,
                     InfluxSourceLBTiming)
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
        InfluxSource(msg_service, config).start(stop_event),
        InfluxSourceLBTiming(msg_service, config).start(stop_event),
        InfluxSourceLBDOWN(msg_service, config).start(stop_event),
        InfluxSourceLBDOWNFailCount(msg_service, config).start(stop_event),
        InfluxSourceDiskStateRead(msg_service, config).start(stop_event),
        InfluxSourceDiskStateWrite(msg_service, config).start(stop_event),
        InfluxSourceDiskStateReadSFS(msg_service, config).start(stop_event),
        InfluxSourceDiskStateWriteSFS(msg_service, config).start(stop_event)
    ])
