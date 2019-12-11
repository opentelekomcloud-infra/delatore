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
    query = 'SELECT * from lb_timing LIMIT 1;'
    lb_timing = client.query(query)
    if  lb_timing.error == None:
        last_time = lb_timing.raw['series'][0]['values'][0][0]

if __name__ == '__main__':
    connection(host='influx1.eco.tsi-dev.otc-service.com',
               username='csm',
               password='*]Hs8vTPsI9?',
               db='csm')
