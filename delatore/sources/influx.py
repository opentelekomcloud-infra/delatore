import logging
import os
import re
from datetime import datetime

from influxdb import InfluxDBClient

from .base import Source
from ..emoji import Emoji, replace_emoji
from ..json2mdwn import convert

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)


class InfluxSource(Source):
    def __init__(self):
        self.host = 'influx1.eco.tsi-dev.otc-service.com'
        self.username = 'csm'
        self.password = os.environ['INFLUX_PASSWORD']
        self.db = 'csm'
        self.port = 8086

    EMOJI_MAP = {
        '`OK`': Emoji.SUCCESS,
        '`FAIL`': Emoji.FAILED,
        '`NO_DATA`': Emoji.NO_DATA,
    }

    @classmethod
    def convert(cls, data: dict) -> str:
        data.pop('From', None)
        text = convert(data)
        text = '** From InfluxDB **\n' + replace_emoji(text, cls.EMOJI_MAP)
        return text.strip()

    def get_influx_statuses(self):
        client = InfluxDBClient(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            database=self.db,
            ssl=True,
            verify_ssl=True)

        proof_of_work = dict(LB_LOAD=get_status(client, 'lb_timing'),
                             LB_DOWN=get_status(client, 'lb_down_test'),
                             SCSI_HDD_TEST=get_status(client, 'iscsi_connection'),
                             RDS_TEST=get_status(client, 'ce_result'))
        return proof_of_work


def get_status(client, entity):
    query = f'SELECT LAST(*) FROM {entity} LIMIT 1;'
    try:
        last_record = client.query(query)
        last_time = last_record.raw['series'][0]['values'][0][0]
        last_time_ms = _convert_time(last_time)
        if (datetime.utcnow() - last_time_ms).total_seconds() < 300:
            return 'OK'
        return 'FAIL'
    except KeyError:
        return 'NO_DATA'


class InfluxTimestampParseException(Exception):
    """Error during Influx timestamp parsing"""


def _convert_time(timestamp):
    time_groups = re.match(r'(.+)\.(\d+)(Z)', timestamp)
    if time_groups is None:
        raise InfluxTimestampParseException
    time_groups = time_groups.groups()
    return datetime.strptime(f'{time_groups[0]}.{time_groups[1][:6]:<06}{time_groups[2]}', '%Y-%m-%dT%H:%M:%S.%fZ')
