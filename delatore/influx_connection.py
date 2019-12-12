import datetime
import re

from influxdb import InfluxDBClient


def connection(host, username, password, db, port=8086):
    client = InfluxDBClient(
        host=host,
        port=port,
        username=username,
        password=password,
        database=db,
        ssl=True,
        verify_ssl=True)
    lb_timing = client.query("SELECT last(*) from lb_timing LIMIT 1")
    if lb_timing.error is None:
        last_time = lb_timing.raw['series'][0]['values'][0][0]
        last_time_ms = datetime.datetime.strptime(re.sub(r"[.]\d{9}", ".000000", last_time), '%Y-%m-%dT%H:%M:%S.%fZ')
        now = datetime.datetime.utcnow()
        delta = now - last_time_ms


if __name__ == '__main__':
    connection(host='influx1.eco.tsi-dev.otc-service.com',
               username='csm',
               password='*]Hs8vTPsI9?',
               db='csm')
