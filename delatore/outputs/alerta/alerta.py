import asyncio
import logging

from apubsub import Service

from delatore.configuration import DEFAULT_INSTANCE_CONFIG, InstanceConfig

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)


class AlertaRunner:
    """Alerta runner"""

    def __init__(self, msg_service: Service, stop_event: asyncio.Event,
                 config: InstanceConfig = DEFAULT_INSTANCE_CONFIG):
        self.client = msg_service.get_client()
        self.stop_event = stop_event
        self.config = config
        self.alerta_key = config.
