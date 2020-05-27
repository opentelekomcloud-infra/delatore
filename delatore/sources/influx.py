"""Influx sources"""
import asyncio
import json
import logging
import re
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from statistics import StatisticsError, mean
from typing import Dict, List, NamedTuple, Optional

import aiohttp
from aiohttp_socks import ProxyConnector
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError, InfluxDBServerError
from influxdb.resultset import ResultSet
from ocomone import Resources

from .base import Source, SourceMeta
from ..unified_json import (Status, UNIFIED_TIME_PATTERN, generate_error, generate_message, generate_status,
                            generate_status_for_host)

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
_CONFIGS = Resources(__file__)


class AsyncInfluxClient(InfluxDBClient):  # pragma: no cover
    """Influx client using aiohttp instead of requests"""

    # pylint: disable=too-many-arguments

    def __init__(self, *args, proxy='', **kwargs):
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

        # noinspection PyTypeChecker
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


class InfluxSourceMeta(SourceMeta):
    """Metaclass for InfluxSource setting params"""

    def __init__(cls, *args, **kwargs):
        SourceMeta.__init__(cls, *args, **kwargs)
        params = cls.config.params
        metrics = params.pop('metrics')
        metrics = [Metric(**met) for met in metrics]
        cls._params = InfluxParams(metrics=metrics, **params)


def _err_message_template(mes_file):
    with open(_CONFIGS[mes_file], 'r') as file:
        str_template = file.read()
    return str_template


class InfluxSource(Source, metaclass=InfluxSourceMeta):
    """InfluxDB client"""

    CONFIG_ID = 'influxdb'
    _params: InfluxParams
    _error_message_template: str = None
    _influx_client = None

    @property
    def _metrics(self):
        return self._params.metrics

    @property
    def influx_client(self):
        """Return new instance of influx client"""
        if self._influx_client is None:
            params = self._params
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


class _InfluxTimingAuxMetrics(NamedTuple):
    """Metrics storage"""

    cpu_utilization: float = -1
    network_bytes_recv: float = -1
    network_bytes_send: float = -1

    @classmethod
    def length(cls) -> int:
        """Get length of internal tuple"""
        return len(cls._fields)


class InfluxSourceLBTiming(InfluxSource):
    """InfluxSourceLBTiming client"""

    # pylint: disable=unused-variable

    CONFIG_ID = 'influxdb_lb_timing'
    _host_timings: Dict[str, deque] = {}
    DEQUE_SIZE = 5

    threshold = 30
    _error_message_template = _err_message_template('error_message_lb_timing.txt')

    async def get_update(self) -> dict:
        main_metric = self._metrics[0]
        host_statuses = await self._get_status(main_metric)
        results = []
        faulty = []
        for host, status in host_statuses.items():
            if status[0] == Status.FAIL:
                results.append(generate_status_for_host(main_metric.name, host, status[0],
                                                        status[1].strftime(UNIFIED_TIME_PATTERN)))
            else:
                if min(self._host_timings[host]) > self.threshold:
                    faulty.append(host)
        if faulty:
            state = await self._get_auxiliary_metrics()  # get overall host state
            for host in faulty:
                results.append(generate_error(self.CONFIG_ID, self._get_error_message(host, state)))
        return generate_message(self.CONFIG_ID, results)

    async def _get_auxiliary_metrics(self) -> Dict[str, _InfluxTimingAuxMetrics]:
        """Return hosts with results of predefined diagnostic queries for each host"""
        list_queries = [met.query.format(entity=met.metric_id) for met in self._metrics[1:]]
        results = await asyncio.gather(*[
            self.influx_client.query(query) for query in list_queries
        ])
        host_results = {}
        for host in self._host_timings:
            host_results[host] = []
        for result in results:
            host_series = zip(self._host_timings.keys(), result.raw['series'])
            for host, series in host_series:
                host_results[host].append(series['values'][0][1])
        for host in host_results:
            res = host_results[host][:_InfluxTimingAuxMetrics.length()]  # use only defined metrics
            host_results[host] = _InfluxTimingAuxMetrics(*res)
        return host_results

    def _get_error_message(self, host, aux_metrics: Dict[str, _InfluxTimingAuxMetrics]):
        try:
            current_response_time = f'{round(mean(self._host_timings[host]))}'
        except StatisticsError:
            current_response_time = 'No data'
        host_state = aux_metrics[host]
        if host_state is None:
            return f'Invalid aux metrics for host {host}'
        return self._error_message_template.format(
            threshold=self.threshold,
            current_response_time=current_response_time,
            hostname=host,
            cpu_utilization=round(host_state.cpu_utilization, 3),
            network_bytes_recv=round(host_state.network_bytes_recv / 1000, 2),
            network_bytes_send=round(host_state.network_bytes_send / 1000, 2))

    async def _get_status(self, metric):
        """Generate status, line per server"""
        query = metric.query.format(entity=metric.metric_id)
        last_record = await self.influx_client.query(query)
        last_time_ms = None
        if not self._host_timings:
            for series in last_record.raw['series']:
                host = series['tags']['server']
                self._host_timings[host] = deque([], self.DEQUE_SIZE)

        statuses = {}
        for series in last_record.raw['series']:
            try:
                hostname = series['tags']['server']
            except KeyError:
                continue
            try:
                query_time = series['values'][0][0]
                last_time_ms = _convert_time(query_time)
                server_response_time = series['values'][0][1]
                self._host_timings[hostname].append(server_response_time)
                now = datetime.utcnow().timestamp()
                status = Status.OK
                if now - last_time_ms.timestamp() > metric.timeout:
                    status = Status.FAIL
                statuses[hostname] = (status, last_time_ms)
            except (KeyError, IndexError):
                statuses[hostname] = (Status.NO_DATA, last_time_ms)
        return statuses


class InfluxSourceLBDOWN(InfluxSource):
    """InfluxSourceLBDOWN client"""

    # pylint: disable=unused-variable

    CONFIG_ID = 'influxdb_lb_down'
    _error_message_template = _err_message_template('error_message_lb_down.txt')

    async def get_update(self) -> dict:
        main_metric = self._metrics[0]
        error_script_status, last_time_ms, status = await self._get_status(main_metric)
        results = []
        if error_script_status:
            if status == status.FAIL:
                results.append(generate_status(main_metric.name, status,
                                               last_time_ms.strftime(UNIFIED_TIME_PATTERN)))
            else:
                results.append(generate_error(main_metric.name, self._error_message_template))
        return generate_message(self.CONFIG_ID, results)

    async def _get_status(self, metric):
        query = metric.query.format(entity=metric.metric_id)
        last_record = await self.influx_client.query(query)
        last_time_ms = None
        status = Status.OK
        if 'series' in last_record.raw:
            error_script_status = True
            last_time = last_record.raw['series'][0]['values'][0][0]
            now = datetime.utcnow().timestamp()
            last_time_ms = _convert_time(last_time)
            if now - last_time_ms.timestamp() > metric.timeout:
                status = Status.FAIL
        else:
            error_script_status = False
        return error_script_status, last_time_ms, status


class InfluxSourceLBDOWNFailCount(InfluxSource):
    """InfluxSourceLBDOWNFailCount client"""

    # pylint: disable=attribute-defined-outside-init

    CONFIG_ID = 'influxdb_lb_failed_requests_to_host'
    _error_message_template = _err_message_template('error_message_lb_down_fail_count.txt')
    _fail_count: deque = None
    threshold_size = 5
    threshold = 5

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._fail_count = deque([0] * self.threshold_size, self.threshold_size)

    async def get_update(self) -> dict:
        status = await self._get_status(self._metrics[0])
        if status is None:
            status = {}
        return generate_message(self.CONFIG_ID, [status])

    async def _get_status(self, metric) -> Optional[dict]:
        query = metric.query.format(entity=metric.metric_id)
        last_record = await self.influx_client.query(query)
        try:
            series = last_record.raw['series'][0]
            hostname = series['tags']['host']
            values = series['values'][0]
            last_time = values[0]
            self._fail_count.append(values[1])
        except (KeyError, IndexError):
            return generate_status(metric.name, Status.NO_DATA, None)

        if min(self._fail_count) > self.threshold:  # if there are at least one error per minute for 5 minutes
            return generate_error(metric.name, self._get_error_message(hostname))

        now = datetime.utcnow().timestamp()
        last_time_ms = _convert_time(last_time)
        if now - last_time_ms.timestamp() > metric.timeout:
            return generate_status(metric.name, Status.FAIL, last_time_ms.strftime(UNIFIED_TIME_PATTERN))
        return None

    def _get_error_message(self, host):
        str_template = self._error_message_template.format(hostname=host)
        return str_template


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
