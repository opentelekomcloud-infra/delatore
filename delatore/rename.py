import datetime
import re

from influxdb import InfluxDBClient

from delatore.bot import Delatore

bot = Delatore()


def connection(host, username, password, db, port=8086):
    client = InfluxDBClient(
        host=host,
        port=port,
        username=username,
        password=password,
        database=db,
        ssl=True,
        verify_ssl=True)

    proof_of_work = dict(lb_timing_measurement=get_time_delta(client, 'lb_timing'),
                         lb_down_test_measurement=get_time_delta(client, 'lb_down_test'),
                         iscsi_connection_measurement=get_time_delta(client, 'iscsi_connection'),
                         ce_result_measurement=get_time_delta(client, 'ce_result'))
    bot.send_message(proof_of_work)


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
    except ValueError:
        return "NO DATA"
    except KeyError:
        return "NO DATA"


if __name__ == '__main__':
    connection(host='influx1.eco.tsi-dev.otc-service.com',
               username='csm',
               password='',
               db='csm')
