import datetime
import re

from influxdb import InfluxDBClient

from delatore.sources.base_source import BaseSource


class Influx(BaseSource):

    def connection(self, host, username, password, db, port=8086):
        client = InfluxDBClient(
            host=host,
            port=port,
            username=username,
            password=password,
            database=db,
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
        last_time_ms = datetime.datetime.strptime(re.sub(r"[.]\d{9}", ".000000", last_time), '%Y-%m-%dT%H:%M:%S.%fZ')
        if (datetime.datetime.utcnow() - last_time_ms).total_seconds() < 300:
            return "OK"
        else:
            return "FAIL"
    except KeyError:
        return "NO DATA"
