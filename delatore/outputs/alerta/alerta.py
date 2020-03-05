import asyncio
import json
import logging

from alertaclient.api import Client
from apubsub import Service

from ...configuration import OUTPUTS_CFG
from ...configuration.dynamic import DEFAULT_INSTANCE_CONFIG, InstanceConfig
from ...outputs.telegram.json2mdwn import convert

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

TG_CONFIG = OUTPUTS_CFG['alerta']


class AlertaRunner:
    """Alerta runner wrapper"""
    _alerta: Client = None

    def __init__(self, msg_service: Service, stop_event: asyncio.Event,
                 config: InstanceConfig = DEFAULT_INSTANCE_CONFIG):
        self.client = msg_service.get_client()
        self.stop_event = stop_event
        self.config = config
        self.alerta_api_key = config.alerta_key

    @property
    def alerta(self):
        """Return alerta instance, create new if missing"""
        if self._alerta is None:
            LOGGER.warning('No alerta exist. Create alerta.')
            self._alerta = Client(key=self.alerta_api_key)
        return self._alerta

    async def alert(self, message):
        """Send message to chat alerting users"""
        LOGGER.debug('Alerta message sent: ')
        alerta_message = {}
        for record in message:
            if record['status'] == 'FAIL':
                alerta_message += record
        return await self.alerta.send_alert(environment=TG_CONFIG.environment,
                                            service=TG_CONFIG.service,
                                            resource=alerta_message['resource'],
                                            event=alerta_message['event'],
                                            value=alerta_message['value'])

    async def remove(self, alert_id):
        """Remove message from alerta"""
        LOGGER.debug('Alerta %s removed from table', alert_id)
        return await self.alerta.delete_alert(alert_id)

    async def start_posting(self):
        """Start posting updates to channel"""
        await self.client.start_consuming()
        topics = TG_CONFIG.subscriptions
        await asyncio.wait([
            self.client.subscribe(topic) for topic in topics
        ])
        LOGGER.info('Alerta subscribed to topics: %s', topics)
        while not self.stop_event.is_set():
            # message consumed
            message = await self.client.get(.1)
            if message is not None:
                data = json.loads(message)
                try:
                    await self.alert(convert(data))  # check if TG response was 200
                except Exception:  # pylint:disable=broad-except
                    LOGGER.exception('Failed to send message %s', data)

    async def _stopper(self):
        while not self.stop_event.is_set():
            await asyncio.sleep(.1)
        self.client.stop_getting()

    async def start(self):
        """Start alerta"""
        await asyncio.wait([
            self.start_posting(),
            self._stopper(),
        ])
