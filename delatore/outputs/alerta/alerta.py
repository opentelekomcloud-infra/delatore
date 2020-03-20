import asyncio
import json
import logging
import threading

from alertaclient.api import Client
from apubsub import Service

from ...configuration import OUTPUTS_CFG, SOURCES_CFG
from ...configuration.dynamic import DEFAULT_INSTANCE_CONFIG, InstanceConfig

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

ALERTA_CONFIG = OUTPUTS_CFG['alerta']
STATUS = 'status'


def get_name_timeout(conf):
    result = {}
    for metric in conf.params['metrics']:
        result[metric['name']] = metric['timeout']
    return result


INFLUX_CONFIG = get_name_timeout(SOURCES_CFG['influxdb'])


def create_msg(record):
    return f'{record["name"]} ' \
           f'has status: {record["status"]}, ' \
           f'timeout: {INFLUX_CONFIG.get(record["name"], 0)}s.'


class AlertaRunner:
    """Alerta runner wrapper"""
    _alerta: Client = None
    _alerta_thread: threading.Thread

    def __init__(self, msg_service: Service, stop_event: threading.Event,
                 config: InstanceConfig = DEFAULT_INSTANCE_CONFIG):
        self.client = msg_service.get_client()
        self.stop_event = stop_event
        self.config = config
        self.alerta_api_key = config.alerta_api_key

    @property
    def alerta(self):
        """Return alerta instance, create new if missing"""
        if self._alerta is None:
            LOGGER.warning('No alerta exist. Create client.')
            self._alerta = Client(key=self.alerta_api_key, endpoint=ALERTA_CONFIG.params['endpoint'])
        return self._alerta

    def alert(self, message):
        """Send messages to alerta"""
        alerta_ids = []
        common_args = dict(
            environment=ALERTA_CONFIG.params['environment'],
            service=[self.config.alerta_service],
            resource=f'{ALERTA_CONFIG.params["resource"]}{message["source"]}',
            origin=ALERTA_CONFIG.params['origin']
        )
        for record in message['status_list']:
            if record['status'] in ['fail', 'no_data']:
                report_id = self.alerta.send_alert(
                    event=record["name"],
                    value=create_msg(record),
                    severity=ALERTA_CONFIG.params['severity'],
                    **common_args,
                )[0]
            else:
                report_id = self.alerta.send_alert(
                    event=record["name"],
                    severity='ok',
                    **common_args,
                )[0]
            
            alerta_ids.append(report_id)
            LOGGER.debug('Alerta message sent')
        return alerta_ids

    def get_current_alerts(self, origin):
        return self.alerta.get_alerts([('origin', origin), ('repeat', False)])

    def remove(self, alerta_ids):
        """Remove message from alerta"""
        LOGGER.debug('Alerts removed from table')
        for alerta_id in alerta_ids:
            self.alerta.delete_alert(alerta_id)

    async def start_posting(self):
        """Start posting updates to channel"""
        await self.client.start_consuming()
        topics = ALERTA_CONFIG.subscriptions
        for topic in topics:
            await self.client.subscribe(topic)
        LOGGER.info('Alerta subscribed to topics: %s', topics)
        while not self.stop_event.is_set():
            # message consumed
            message = await self.client.get(.1)
            if message is not None:
                data = json.loads(message)
                self.alert(data)  # check if TG response was 200

    async def _stopper(self):
        while not self.stop_event.is_set():
            await asyncio.sleep(.5)
        await self.client.stop_getting()

    async def start(self):
        """Start alerta"""

        def _main():
            asyncio.run(self.start_posting())

        self._alerta_thread = threading.Thread(target=_main,
                                               name="Alerta-Thread", )
        self._alerta_thread.start()
        await self._stopper()
        self._alerta_thread.join()

    def stop(self, stop_event: threading.Event):
        """Stop alerta"""
        self.stop_event = stop_event
