from ocomone import Resources
import asyncio
import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import List, NamedTuple

import aiohttp
from aiohttp_socks import ProxyConnector
from apubsub.client import Client
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError, InfluxDBServerError
from influxdb.resultset import ResultSet

from .base import Source
from ..configuration import DEFAULT_INSTANCE_CONFIG
from ..unified_json import Status, UNIFIED_TIME_PATTERN, generate_message, generate_status, generate_error

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
_CONFIGS = Resources(__file__)

class AsyncInfluxClient(InfluxDBClient):  # pragma: no cover
    """Influx client using aiohttp instead of requests"""

    # pylint: disable=too-many-arguments

    def __init__(self, *args, proxy="", **kwargs):
        self.proxy: str = proxy
        super().__init__(*args, **kwargs)

    async def query(self,
                    query,
                    params=None,
                    bind_params=None,
                    epoch=None,
                    expected_response_code=200,
                    database=None,
                    raise_errors=True,
                    chunked=False,
                    chunk_size=0,
                    method='GET'):
        if params is None:
            params = {}

        if bind_params is not None:
            params_dict = json.loads(params.get('params', '{}'))
            params_dict.update(bind_params)
            params['params'] = json.dumps(params_dict)

        params['q'] = query
        params['db'] = database or self._database

        if epoch is not None:
            params['epoch'] = epoch

        if chunked:
            params['chunked'] = 'true'
            if chunk_size > 0:
                params['chunk_size'] = chunk_size

        if query.lower().startswith('select ') and ' into ' in query.lower():
            method = 'POST'

        data = await self.request(
            url='query',
            method=method,
            params=params,
            data=None,
            expected_response_code=expected_response_code
        )

        results = [
            ResultSet(result, raise_errors=raise_errors)
            for result
            in data.get('results', [])
        ]

        if len(results) == 1:
            return results[0]

        return results

    async def request(self, url, method='GET', params=None, data=None,
                      expected_response_code=200, headers=None):
        url = f'{self._baseurl}/{url}'

        if headers is None:
            headers = self._headers

        if params is None:
            params = {}

        if isinstance(data, (dict, list)):
            data = json.dumps(data)

        kwargs = dict(
            method=method,
            url=url,
            params=params,
            data=data,
            headers=headers,
            verify_ssl=self._verify_ssl,
            timeout=self._timeout,
        )
        if self._username is not None:
            kwargs.update(auth=aiohttp.BasicAuth(self._username, self._password or ''))

        if self.proxy:
            connector = ProxyConnector.from_url(self.proxy)
        else:
            connector = None

        async with aiohttp.ClientSession(connector=connector, headers=self._session.headers) as session:
            async with session.request(**kwargs) as response:
                data = await response.json()
        # if there's not an error, there must have been a successful response
        if 500 <= response.status < 600:
            raise InfluxDBServerError(data)
        if response.status == expected_response_code:
            return data
        raise InfluxDBClientError(data, response.status)


INFLUX_POLLING_INTERVAL = 60


@dataclass(frozen=True)
class Metric:
    """Metric description"""
    name: str
    metric_id: str
    timeout: int = 300
    query: str = ''


class InfluxParams(NamedTuple):
    """Influx params storage"""
    host: str
    port: int
    username: str
    database: str
    metrics: List[Metric]


class InfluxSource(Source):
    """InfluxDB client"""

    CONFIG_ID = 'influxdb'
    _params: InfluxParams = None

    @classmethod
    def params(cls) -> InfluxParams:
        if cls._params is None:
            params = cls.config.params
            metrics = params.pop('metrics')
            metrics = [Metric(**met) for met in metrics]
            cls._params = InfluxParams(metrics=metrics, **params)
        return cls._params

    def __init__(self, client: Client, instance_config=DEFAULT_INSTANCE_CONFIG):
        super().__init__(client, instance_config=instance_config)
        self._influx_client = None

    @property
    def influx_client(self):
        """Return new instance of influx client"""
        if self._influx_client is None:
            params = self.params()
            self._influx_client = AsyncInfluxClient(
                host=params.host,
                port=params.port,
                username=params.username,
                password=self.instance_config.influx_password,
                database=params.database,
                ssl=True,
                verify_ssl=True,
                proxy=self.instance_config.proxy,
            )
        return self._influx_client

    async def get_update(self) -> dict:
        metrics = self.params().metrics
        results = await asyncio.gather(*[
            self._get_status(met) for met in metrics
        ])
        return generate_message(self.CONFIG_ID, results)

    async def _get_status(self, metric):
        query = metric.query.format(entity=metric.metric_id)
        last_record = await self.influx_client.query(query)
        try:
            last_time = last_record.raw['series'][0]['values'][0][0]
            a = 5
        except KeyError:
            return generate_status(metric.name, Status.NO_DATA, None)
        now = datetime.utcnow().timestamp()
        last_time_ms = _convert_time(last_time)
        if now - last_time_ms.timestamp() < metric.timeout:
            return generate_status(metric.name, Status.OK,
                                   last_time_ms.strftime(UNIFIED_TIME_PATTERN))
        return generate_status(metric.name, Status.FAIL,
                               last_time_ms.strftime(UNIFIED_TIME_PATTERN))


class InfluxSourceLBTiming(InfluxSource):
    CONFIG_ID = 'influxdb_lb_timing'
    _params: InfluxParams = None
    list_elapsed_time = [70, 70, 70, 70, 70]

    @classmethod
    def params(cls) -> InfluxParams:
        if cls._params is None:
            params = cls.config.params
            metrics = params.pop('metrics')
            metric_in_list = []
            for met in metrics:
                if met['metric_id'] == 'lb_timing':
                    metric = Metric(**met)
                    if metric is not None:
                        metric_in_list.append(metric)
                if met['metric_id'] == 'cpu_utilization':
                    metric = Metric(**met)
                    if metric is not None:
                        metric_in_list.append(metric)
                if met['metric_id'] == 'node_distribution':
                    metric = Metric(**met)
                    if metric is not None:
                        metric_in_list.append(metric)
                if met['metric_id'] == 'network_bytes_recv':
                    metric = Metric(**met)
                    if metric is not None:
                        metric_in_list.append(metric)
                if met['metric_id'] == 'network_bytes_send':
                    metric = Metric(**met)
                    if metric is not None:
                        metric_in_list.append(metric)
            cls._params = InfluxParams(metrics=metric_in_list, **params)
        return cls._params

    async def get_update(self) -> dict:
        metrics = self.params().metrics
        last_elapsed_time, last_time_ms, status = await self._get_status(metrics[0])
        self.list_elapsed_time.pop(0)
        self.list_elapsed_time.append(last_elapsed_time)
        results = []
        if min(self.list_elapsed_time) < 60:
            results.append(generate_status(metrics[0].name, status,
                                           last_time_ms.strftime(UNIFIED_TIME_PATTERN)))
        else:
            results.append(generate_error('InfluxdbLBTiming', await self._get_error_message(metrics)))
        return generate_message(self.CONFIG_ID, results)

    async def _get_error_message(self, metrics):
        with open(_CONFIGS['error_message_lb_timing.txt'], 'r') as myfile:
            str_template = myfile.read()
            cpu_utilization_query = metrics[1].query.format(entity=metrics[1].metric_id)
            node_distribution_query = metrics[2].query.format(entity=metrics[2].metric_id)
            network_bytes_recv_query = metrics[3].query.format(entity=metrics[3].metric_id)
            network_bytes_send_query = metrics[4].query.format(entity=metrics[4].metric_id)
        result_query1, result_query2, result_query3, result_query4 = await asyncio.gather(
            self.influx_client.query(cpu_utilization_query),
            self.influx_client.query(node_distribution_query),
            self.influx_client.query(network_bytes_recv_query),
            self.influx_client.query(network_bytes_send_query))
        str_template.format(result_query1=result_query1,
                            result_query2=result_query2,
                            result_query3=result_query3,
                            result_query4=result_query4)
        return str_template

    async def _get_status(self, metric):
        query = metric.query.format(entity=metric.metric_id)
        last_record = await self.influx_client.query(query)
        try:
            last_time = last_record.raw['series'][0]['values'][0][0]
            last_elapsed_time = last_record.raw['series'][0]['values'][0][1]
        except KeyError:
            return generate_status(metric.name, Status.NO_DATA, None)
        now = datetime.utcnow().timestamp()
        last_time_ms = _convert_time(last_time)
        status = Status.OK
        if now - last_time_ms.timestamp() > metric.timeout:
            status = Status.FAIL
        return last_elapsed_time, last_time_ms, status


class InfluxTimestampParseException(Exception):
    """Error during Influx timestamp parsing"""


_RE_TIME_GROUPS = re.compile(r'(.+)\.(\d+)(Z)')
_RE_TIME_GROUPS_WITHOUT_MS = re.compile(r'(.+)(Z)')
TIME_PATTERN = '%Y-%m-%dT%H:%M:%S.%fZ'


def _convert_time(timestamp) -> datetime:
    match_ts = _RE_TIME_GROUPS.match(timestamp)
    if match_ts is None:
        match_ts = _RE_TIME_GROUPS_WITHOUT_MS.match(timestamp)
        if match_ts is None:
            raise InfluxTimestampParseException
        timestamp, timezone = match_ts.groups()
        dtime = datetime.strptime(f'{timestamp}.123456{timezone}', TIME_PATTERN)
        return dtime
    timestamp, nsec, timezone, *_ = match_ts.groups()
    msec = nsec[:6]
    dtime = datetime.strptime(f'{timestamp}.{msec}{timezone}', TIME_PATTERN)
    return dtime
