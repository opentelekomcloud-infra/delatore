import os
from datetime import datetime

from influxdb import InfluxDBClient

from .base import Source
from ..emoji import Emoji, replace_emoji
from ..json2mdwn import convert


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

        proof_of_work = dict(CSM_LB_LOAD=get_time_delta(client, 'lb_timing'),
                             CSM_LB_DOWN=get_time_delta(client, 'lb_down_test'),
                             CSM_SCSI_HDD_TEST=get_time_delta(client, 'iscsi_connection'),
                             CSM_RDS_TEST=get_time_delta(client, 'ce_result'))
        return proof_of_work


def get_time_delta(client, entity):
    query = f"SELECT LAST(*) FROM {entity} LIMIT 1;"
    try:
        last_record = client.query(query)
        last_time = last_record.raw['series'][0]['values'][0][0]
        time_parts = last_time.split('.')
        time_zone = ''
        for item in time_parts[1]:
            if item.isalpha():
                time_zone += item
        second_part = '.123456' + time_zone
        last_time_ms = datetime.strptime(time_parts[0] + second_part, f'%Y-%m-%dT%H:%M:%S.%f{time_zone}')
        if (datetime.utcnow() - last_time_ms).total_seconds() < 300:
            return "OK"
        return "FAIL"
    except KeyError:
        return "NO_DATA"
