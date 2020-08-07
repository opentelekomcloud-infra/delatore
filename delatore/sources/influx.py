"""Influx sources"""
import asyncio
import json
import logging
import re
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from statistics import StatisticsError, mean
from typing import Dict, List, NamedTuple
from jinja2 import Template

import aiohttp
from aiohttp_socks import ProxyConnector
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError, InfluxDBServerError
from influxdb.resultset import ResultSet
from ocomone import Resources

from .base import Source, SourceMeta
from ..unified_json import (Status, UNIFIED_TIME_PATTERN, generate_disk_status, generate_error, generate_host_status,
                            generate_message, generate_status)

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
_CONFIGS = Resources(__file__)


class AsyncInfluxClient(InfluxDBClient):  # pragma: no cover
    """Influx client using aiohttp instead of requests"""

    # pylint: disable=too-many-arguments

    def __init__(self, *args, proxy='', **kwargs):
        self.proxy: str = proxy
        super().__init__(*args, **kwargs)

    # pylint:disable=invalid-overridden-method
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

    # pylint:disable=invalid-overridden-method
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
        metrics = params['metrics']
        metrics = [Metric(**met) for met in metrics]
        cls._params = InfluxParams(metrics=metrics, host=params['host'], port=params['port'],
                                   username=params['username'], database=params['database'])


def _get_error_template(mes_file):
    with open(_CONFIGS[mes_file], 'r') as file:
        str_template = file.read()
    return str_template


class InfluxSource(Source, metaclass=InfluxSourceMeta):
    """InfluxDB client"""

    CONFIG_ID = 'influxdb'
    _params: InfluxParams
    _error_template: str = None
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
        status = Status.FAIL
        if now - last_time_ms.timestamp() < metric.timeout:
            status = Status.OK
        return generate_status(metric.name, status, last_time_ms.strftime(UNIFIED_TIME_PATTERN))


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

    CONFIG_ID = 'influxdb_lb_timing'
    _host_timings: Dict[str, deque] = {}
    DEQUE_SIZE = 5

    threshold = 60
    _error_template = _get_error_template('error_lb_timing.txt')

    async def get_update(self) -> dict:
        main_metric = self._metrics[0]
        host_statuses = await self._get_status(main_metric)
        results = []
        faulty = []
        for host, info in host_statuses.items():
            if info[0] != Status.OK:
                results.append(
                    generate_host_status(main_metric.name, host, info[0], info[1].strftime(UNIFIED_TIME_PATTERN)))
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
        return self._error_template.format(
            threshold=self.threshold,
            current_response_time=current_response_time,
            hostname=host,
            cpu_utilization=round(host_state.cpu_utilization, 3),
            network_bytes_recv=round(host_state.network_bytes_recv / 1000, 2),
            network_bytes_send=round(host_state.network_bytes_send / 1000, 2)
        )

    async def _get_status(self, metric):
        """Generate status, line per server"""
        query = metric.query.format(entity=metric.metric_id)
        last_record = await self.influx_client.query(query)
        if not self._host_timings:
            for series in last_record.raw['series']:
                host = series['tags']['server']
                self._host_timings[host] = deque([], self.DEQUE_SIZE)
        statuses = {}
        for series in last_record.raw['series']:
            try:
                host = series['tags']['server']
                last_time, response_time, *_ = series['values'][0]
            except(KeyError, IndexError):
                continue
            last_time_ms = _convert_time(last_time)
            self._host_timings[host].append(response_time)
            now = datetime.utcnow().timestamp()
            status = Status.OK
            if now - last_time_ms.timestamp() > metric.timeout:
                status = Status.FAIL
            statuses[host] = (status, last_time_ms)
        return statuses


class InfluxSourceLBDOWN(InfluxSource):
    """InfluxSourceLBDOWN client"""

    CONFIG_ID = 'influxdb_lb_down'
    _error_template = _get_error_template('error_lb_down.txt')

    async def get_update(self) -> dict:
        metric = self._metrics[0]
        status, last_time_ms, control_value = await self._get_status(metric)
        results = []
        if status != Status.OK:
            results.append(generate_status(metric.name, status, last_time_ms.strftime(UNIFIED_TIME_PATTERN)))
        else:
            if control_value == 1:
                results.append(generate_error(self.CONFIG_ID, self._error_template))

        return generate_message(self.CONFIG_ID, results)

    async def _get_status(self, metric):
        query = metric.query.format(entity=metric.metric_id)
        last_record = await self.influx_client.query(query)
        status = Status.OK
        last_time_ms = None
        control_value = 1
        if 'series' in last_record.raw:
            last_time, control_value, *_ = last_record.raw['series'][0]['values'][0]
            now = datetime.utcnow().timestamp()
            last_time_ms = _convert_time(last_time)
            if now - last_time_ms.timestamp() > metric.timeout:
                status = Status.FAIL
        return status, last_time_ms, control_value


class InfluxSourceLBDOWNFailCount(InfluxSource):
    """InfluxSourceLBDOWNFailCount client"""

    CONFIG_ID = 'influxdb_lb_down_fail_requests'
    _error_template = _get_error_template('error_lb_down_fail_count.txt')
    _fail_count: deque = None
    _threshold_size = 5

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._fail_count = deque([0] * self._threshold_size, self._threshold_size)

    async def get_update(self) -> dict:
        metric = self._metrics[0]
        host, status, last_time_ms = await self._get_status(self._metrics[0])
        results = []
        if status != Status.OK:
            results.append(generate_status(metric.name, status, last_time_ms.strftime(UNIFIED_TIME_PATTERN)))
        else:
            if min(self._fail_count) > self._threshold_size:  # if there are at least one error per minute for 5 minutes
                results.append(generate_error(metric.name, self._get_error_message(host)))

        return generate_message(self.CONFIG_ID, results)

    async def _get_status(self, metric):
        query = metric.query.format(entity=metric.metric_id)
        last_record = await self.influx_client.query(query)
        try:
            series = last_record.raw['series'][0]
            host = series['tags']['host']
            last_time, fail_count, *_ = series['values'][0]
            self._fail_count.append(fail_count)
        except (KeyError, IndexError):
            raise InfluxQueryResultsException
        now = datetime.utcnow().timestamp()
        last_time_ms = _convert_time(last_time)
        status = Status.OK
        if now - last_time_ms.timestamp() > metric.timeout:
            status = Status.FAIL
        return host, status, last_time_ms

    def _get_error_message(self, host):
        str_template = self._error_template.format(hostname=host)
        return str_template


def _get_disk_info(target_value, last_time, timeout) -> List:
    disk_info = [target_value]
    now = datetime.utcnow().timestamp()
    last_time_ms = _convert_time(last_time)
    disk_info.append(last_time_ms)
    status = Status.OK
    if now - last_time_ms.timestamp() > timeout:
        status = Status.FAIL
    disk_info.append(status)
    return disk_info


class InfluxSourceDiskStateRead(InfluxSource):
    """InfluxSourceDiskStateRead client"""

    CONFIG_ID = 'influxdb_disk_state'
    text_message = 'for {device} not allowed read operations'
    _error_template = _get_error_template('error_disk_state.txt')
    devices = ('vdb', 'vdc', 'vdd', 'sda',)
    hosts = (
        'scn3-5-initiator-instance',
        'test-scn3-eu-de-01',
        'test-scn3-eu-de-02',
        'test-scn3-eu-de-03',
    )
    entity = 'diskio'
    column = 'reads'

    scenario_names = {
        ('sda',): 'SCSI_HDD_TEST',
        ('vdb', 'vdc', 'vdd',): 'HDD_TEST',
    }

    async def get_update(self):
        main_metric = self._metrics[0]
        disk_statuses = await self._get_status(main_metric)
        results = []
        aux_metric = await self.get_auxiliary_metrics()

        for host in disk_statuses.keys():
            for device in disk_statuses[host].keys():
                if disk_statuses[host][device][2] != Status.OK:
                    results.append(
                        generate_disk_status(main_metric.name,
                                             host,
                                             device,
                                             disk_statuses[host][device][2],
                                             disk_statuses[host][device][1].strftime(UNIFIED_TIME_PATTERN)))
                else:
                    if disk_statuses[host][device][0] <= 0:
                        results.append(
                            generate_error(main_metric.name, self.get_error_message(host, device, aux_metric)))

        return generate_message(self.__class__.__name__, results)

    def get_error_message(self, host, device, auxiliary_metrics):
        text_message = self.text_message.format(device=device)
        scenario_name = self.determine_scenario_name(device)
        try:
            str_template = self._error_template.format(text_message=text_message,
                                                       hostname=host,
                                                       scenario_name=scenario_name,
                                                       cpu=round(auxiliary_metrics[host][0], 2),
                                                       memory=round(auxiliary_metrics[host][1], 2))
        except (IndexError, KeyError):
            str_template = ('No data about current cpu utilization '
                            'and current memory utilization '
                            'for {device} on {host}'.format(device=device, host=host))
        return str_template

    def determine_scenario_name(self, device):
        scenario_name = None
        for key in self.scenario_names.keys():
            if device in key:
                scenario_name = self.scenario_names[key]
        return scenario_name

    async def get_auxiliary_metrics(self):
        list_queries = [met.query.format(entity=met.metric_id) for met in self._metrics[1:]]
        results = await asyncio.gather(*[
            self.influx_client.query(query) for query in list_queries
        ])
        aux_metric = {host: [] for host in self.hosts}
        for result in results:
            for series in result.raw['series']:
                try:
                    host = series['tags']['host']
                    value = series['values'][0][1]
                    aux_metric[host].append(value)
                except (IndexError, KeyError):
                    continue
        return aux_metric

    async def _get_status(self, metric):
        query = metric.query.format(entity=self.entity,
                                    column=self.column,
                                    additional_condition='')
        last_record = await self.influx_client.query(query)
        disk_statuses = {host: {} for host in self.hosts}
        for series in last_record.raw['series']:
            try:
                host = series['tags']['host']
                device = series['tags']['name']
                target_value = series['values'][0][1]
                last_time = series['values'][0][0]
            except (IndexError, KeyError):
                continue
            if device in self.devices and host in self.hosts:
                disk_statuses[host][device] = _get_disk_info(target_value, last_time, metric.timeout)
        return disk_statuses


class InfluxSourceDiskStateWrite(InfluxSourceDiskStateRead):
    """InfluxSourceDiskStateWrite client"""

    text_message = 'for {device} not allowed write operations'
    column = 'writes'


class InfluxSourceDiskStateReadSFS(InfluxSourceDiskStateRead):
    """InfluxSourceDiskStateReadSFS client"""

    devices = ('sfs',)
    hosts = ('scn3-5-test-bastion',)
    entity = 'nfsiostat'
    column = 'ops_sec'
    scenario_names = {
        ('sfs',): 'SFS_WITH_ENCRYPTION'
    }
    additional_condition = 'AND type=~/read/'

    async def _get_status(self, metric):
        query = metric.query.format(entity=self.entity,
                                    column=self.column,
                                    additional_condition=self.additional_condition)
        last_record = await self.influx_client.query(query)
        disk_statuses = {host: {} for host in self.hosts}
        for series in last_record.raw['series']:
            try:
                host = series['tags']['host']
                target_value = series['values'][0][1]
                device = self.devices[0]
                last_time = series['values'][0][0]
            except (IndexError, KeyError):
                continue
            if host in self.hosts:
                disk_statuses[host][device] = _get_disk_info(target_value, last_time, metric.timeout)
        return disk_statuses


class InfluxSourceDiskStateWriteSFS(InfluxSourceDiskStateReadSFS):
    """InfluxSourceDiskStateWriteSFS client"""

    additional_condition = 'AND type=~/write/'


class InfluxSourceSFSStatus(InfluxSourceLBDOWN):
    """InfluxSourceSFSStatus client"""

    CONFIG_ID = 'influxdb_sfs_status'
    _error_template = _get_error_template('error_sfs_status.txt')


class InfluxSourceAutoscaling(InfluxSource):
    """InfluxSourceAutoscallingclient"""

    CONFIG_ID = 'influxdb_autoscaling'
    _threshold = 30
    _error_message_template = _get_error_template('error_message_autoscaling.txt')

    async def get_update(self) -> dict:
        main_metric = self._metrics[0]
        error_status, last_time_ms, status = await self._get_status(main_metric)
        results = []
        if status == status.FAIL:
            results.append(generate_status(main_metric.name, status,
                                           last_time_ms.strftime(UNIFIED_TIME_PATTERN)))
        if status == status.NO_DATA:
            results.append(generate_status(main_metric.name, status, None))
        else:
            if error_status:
                auxilary_metric = self._metrics[1]
                cpu_utilization = await self._get_auxilary_metrics(auxilary_metric)
                results.append(generate_error(main_metric.name,
                                              self._error_message_template.format(threshold=self._threshold,
                                                                                  cpu_utilization=cpu_utilization)))
        return generate_message(self.CONFIG_ID, results)

    async def _get_auxilary_metrics(self, metric):
        query = metric.query.format(entity=metric.metric_id)
        result = await self.influx_client.query(query)
        try:
            cpu_utilization = round(result.raw['series'][0]['values'][0][1], 2)
        except(IndexError, KeyError):
            cpu_utilization = 'No data'
        return cpu_utilization

    async def _get_status(self, metric):
        query = metric.query.format(entity=metric.metric_id)
        last_record = await self.influx_client.query(query)
        last_time_ms = None
        error_status = False
        status = Status.OK
        try:
            response_line = last_record.raw['series'][0]['values'][0]
        except(IndexError, KeyError):
            status = Status.NO_DATA
            return error_status, last_time_ms, status
        response_time = response_line[1]
        if response_time is not None:
            if response_time > self._threshold:
                error_status = True
        last_time = response_line[0]
        now = datetime.utcnow().timestamp()
        last_time_ms = _convert_time(last_time)
        if now - last_time_ms.timestamp() > metric.timeout:
            status = Status.FAIL
        return error_status, last_time_ms, status


class InfluxSourceRDSTest(InfluxSource):
    """InfluxSourceRDSTest client"""


    CONFIG_ID = 'influxdb_rds_test'
    _error_message_template = _get_error_template('error_message_rds_test.txt')
    _threshold = 1
    rows = ("tup_fetched", "tup_returned", "tup_inserted", "tup_updated", "tup_deleted")

    async def get_update(self) -> dict:
        main_metric = self._metrics[0]
        error_status, last_time_ms, status = await self._get_status(main_metric)
        results = []
        if error_status:
            if status == status.FAIL or status == status.NO_DATA:
                results.append(generate_status(main_metric.name, status,
                                               last_time_ms.strftime(UNIFIED_TIME_PATTERN)))
            else:
                aux_metrics = await self.get_auxiliary_metrics()
                rows_info = self._get_rows_info(aux_metrics['rows'])
                results.append(generate_error(main_metric.name, self._error_message_template.format(rows=rows_info,
                                                                                                    qps=aux_metrics['qps'])))
        return generate_message(self.CONFIG_ID, results)

    def _get_rows_info(self, rows):
        rows_info = ''
        for key, value in rows.items():
            rows_info += "\n" + "      " + str(key) + " : " + str(value)
        return rows_info

    async def get_auxiliary_metrics(self):
        list_queries = [met.query.format(entity=met.metric_id) for met in self._metrics[1:]]
        aux_metrics = {}
        aux_metrics['rows'] = await self._get_rows(list_queries[0])
        aux_metrics['qps'] = await self._get_qps(list_queries[1])
        return aux_metrics

    async def _get_qps(self, query):
        result = await self.influx_client.query(query)
        try:
            qps = round(result.raw['series'][0]['values'][0][1], 2)
        except(IndexError, KeyError):
            qps = 'No data'
        return qps

    async def _get_rows(self, query):
        row_values = {}
        template_query = Template(query)
        for row in self.rows:
            query_for_row = template_query.render(column_name=row)
            result = await self.influx_client.query(query_for_row)
            try:
                row_values[row] = round(result.raw['series'][0]['values'][0][1], 2)
            except(IndexError, KeyError):
                row_values[row] = 'No data'
        return row_values

    async def _get_status(self, metric):
        query = metric.query.format(entity=metric.metric_id)
        last_record = await self.influx_client.query(query)
        last_time_ms = None
        error_status = False
        status = Status.OK
        try:
            response_line = last_record.raw['series'][0]['values'][0]
        except(IndexError, KeyError):
            status = Status.NO_DATA
            return error_status, last_time_ms, status
        returned_value = response_line[1]
        if returned_value < self._threshold:
            error_status = True
        last_time = response_line[0]
        now = datetime.utcnow().timestamp()
        last_time_ms = _convert_time(last_time)
        if now - last_time_ms.timestamp() > metric.timeout:
            status = Status.FAIL
        return error_status, last_time_ms, status


class InfluxTimestampParseException(Exception):
    """Error during Influx timestamp parsing"""


class InfluxQueryResultsException(Exception):
    """Error during Influx query results parsing"""


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
