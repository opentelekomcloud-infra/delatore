import asyncio
import json
import logging
import re
from datetime import datetime
from typing import Dict

import aiohttp
from aiohttp import BasicAuth
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError, InfluxDBServerError
from influxdb.resultset import ResultSet

from .base import Source
from ..configuration import BOT_CONFIG
from ..emoji import Emoji, replace_emoji
from ..json2mdwn import convert

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)


class AsyncInfluxClient(InfluxDBClient):
    """Influx client using aiohttp instead of requests"""

    def __init__(self, *args, **kwargs):
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

        # TODO(aviau): Always return a list. (This would be a breaking change)
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

        # Try to send the request more than once by default (see #103)
        retry = True
        _try = 0
        kwargs = dict(
            method=method,
            url=url,
            params=params,
            data=data,
            headers=headers,
            verify_ssl=self._verify_ssl,
            timeout=self._timeout
        )
        if self._username is not None:
            kwargs.update(auth=BasicAuth(self._username, self._password or ''))
        async with aiohttp.ClientSession(headers=self._session.headers) as session:
            async with session.request(**kwargs) as response:
                data = await response.json()
        # if there's not an error, there must have been a successful response
        if 500 <= response.status < 600:
            raise InfluxDBServerError(data)
        elif response.status == expected_response_code:
            return data
        else:
            raise InfluxDBClientError(data, response.status)


class InfluxSource(Source):
    def __init__(self):
        self.client = AsyncInfluxClient(
            host='influx1.eco.tsi-dev.otc-service.com',
            port=8086,
            username='csm',
            password=BOT_CONFIG.influx_password,
            database='csm',
            ssl=True,
            verify_ssl=True)

    INFLUX_POLLING_INTERVAL = 60

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

    # noinspection PyBroadException
    async def start(self, stop_event):
        """Start InfluxDB polling"""
        while not stop_event.is_set():
            try:
                self.updates = convert(await self.get_influx_statuses())
            except Exception:  # pylint: disable=broad-except
                LOGGER.exception('Failed to get influx status')
            await asyncio.sleep(self.INFLUX_POLLING_INTERVAL)

    async def get_influx_statuses(self):
        results = await asyncio.gather(
            self._get_status('lb_timing'),
            self._get_status('lb_down_test'),
            self._get_status('iscsi_connection'),
            self._get_status('ce_result'),
        )
        statuses: Dict[str, str] = dict(zip(
            ['LB_LOAD', 'LB_DOWN', 'SCSI_HDD_TEST', 'RDS_TEST'],
            results
        ))
        return statuses

    async def _get_status(self, entity):
        query = f'SELECT LAST(*) FROM {entity} LIMIT 1;'
        try:
            last_record = await self.client.query(query)
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
