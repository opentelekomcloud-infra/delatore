import asyncio
import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import List, NamedTuple
from ocomone import Resources
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
    _error_message_file = None

    @classmethod
    def params(cls) -> InfluxParams:
        if cls._params is None:
            params = cls.config.params
            cls._metrics = params.pop('metrics')
            metrics = [Metric(**met) for met in cls._metrics]
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
        self._metrics = self.params().metrics
        results = await asyncio.gather(*[
            self._get_status(met) for met in self._metrics
        ])
        return generate_message(self.CONFIG_ID, results)

    async def _get_status(self, metric):
        query = metric.query.format(entity=metric.metric_id)
        last_record = await self.influx_client.query(query)
        try:
            last_time = last_record.raw['series'][0]['values'][0][0]
        except KeyError:
            return generate_status(metric.name, Status.NO_DATA, None)
        now = datetime.utcnow().timestamp()
        last_time_ms = _convert_time(last_time)
        if now - last_time_ms.timestamp() < metric.timeout:
            return generate_status(metric.name, Status.OK,
                                   last_time_ms.strftime(UNIFIED_TIME_PATTERN))
        return generate_status(metric.name, Status.FAIL,
                               last_time_ms.strftime(UNIFIED_TIME_PATTERN))

    async def _get_error_message(self):
        with open(_CONFIGS[self._error_message_file], 'r') as file:
            str_template = file.read()
        return str_template


class InfluxSourceLBTiming(InfluxSource):
    CONFIG_ID = 'influxdb_lb_timing'
    _params: InfluxParams = None
    list_elapsed_time = [1, 1, 1, 1, 1]

    _allowed_metrics = {'lb_timing', 'cpu_utilization', 'node_distribution', 'network_bytes_recv', 'network_bytes_send'}
    _values_for_error_message = {'cpu_utilization', 'node_distribution', 'network_bytes_recv', 'network_bytes_send'}

    _threshold = 60

    @property
    def threshold(self):
        return self._threshold

    @threshold.setter
    def threshold(self, threshold):
        self._threshold = threshold


    async def get_update(self) -> dict:
        self._metrics = self.params().metrics
        last_elapsed_time, last_time_ms, status = await self._get_status(self._metrics[0])
        self.list_elapsed_time.pop(0)
        self.list_elapsed_time.append(last_elapsed_time)
        results = []
        if min(self.list_elapsed_time) < self.threshold:
            results.append(generate_status(self._metrics[0].name, status,
                                           last_time_ms.strftime(UNIFIED_TIME_PATTERN)))
        else:
            results.append(generate_error('InfluxdbLBTiming', await self._get_error_message()))
        return generate_message(self.CONFIG_ID, results)

    async def _get_error_message(self):
        with open(_CONFIGS['error_message_lb_timing.txt'], 'r') as file:
            str_template = file.read()
            list_queries = []
        for met in self._metrics[1:]:
            list_queries.append(met.query.format(entity=met.metric_id))
        results_queries = await asyncio.gather(*[
            self.influx_client.query(query) for query in list_queries
        ])
        results_queries_without_empty_lines = []
        for result_query in results_queries:
            try:
                for line in result_query.raw['series'][0]['values']:
                    results_queries_without_empty_lines.append(line[1])
            except KeyError:
                results_queries_without_empty_lines.append('No data')
        str_template = str_template.format(cpu_utilization=round(results_queries_without_empty_lines[0], 3),
                                           node_distribution1=results_queries_without_empty_lines[1],
                                           node_distribution2=results_queries_without_empty_lines[2],
                                           network_bytes_recv=round(results_queries_without_empty_lines[3]/1000, 2),
                                           network_bytes_send=round(results_queries_without_empty_lines[4]/1000, 2))
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


class InfluxSourceLBDOWN(InfluxSource):
    CONFIG_ID = 'influxdb_lb_down'
    _params: InfluxParams = None
    _error_message_file = 'error_message_lb_down.txt'

    async def get_update(self) -> dict:
        self._metrics = self.params().metrics
        error_script_status, last_time_ms, status = await self._get_status(self._metrics[0])
        results = []
        if not error_script_status:
            results.append(generate_status(self._metrics[0].name, status,
                                           last_time_ms.strftime(UNIFIED_TIME_PATTERN)))
        else:
            results.append(generate_error('InfluxdbLBDown', await self._get_error_message() ))
        return generate_message(self.CONFIG_ID, results)

    async def _get_status(self, metric):
        query = metric.query.format(entity=metric.metric_id)
        last_record = await self.influx_client.query(query)
        last_time_ms = None
        status = Status.OK
        error_script_status = False
        if 'series' in last_record.raw:
            error_script_status = True
        else:
            last_time = last_record.raw['series'][0]['values'][0][0]
            now = datetime.utcnow().timestamp()
            last_time_ms = _convert_time(last_time)
            if now - last_time_ms.timestamp() > metric.timeout:
                status = Status.FAIL
        return error_script_status, last_time_ms, status


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
