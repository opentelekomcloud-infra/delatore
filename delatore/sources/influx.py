import asyncio
import json
import logging
import re
from datetime import datetime
from typing import Dict, NamedTuple, Optional

import aiohttp
from aiohttp_socks import ProxyConnector
from apubsub.client import Client
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError, InfluxDBServerError
from influxdb.resultset import ResultSet

from .base import Json, Source
from ..configuration import BOT_CONFIG
from ..emoji import Emoji, replace_emoji
from ..json2mdwn import convert

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)


class AsyncInfluxClient(InfluxDBClient):  # pragma: no cover
    """Influx client using aiohttp instead of requests"""

    # pylint: disable=too-many-arguments

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

        if BOT_CONFIG.proxy:
            connector = ProxyConnector.from_url(BOT_CONFIG.proxy)
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
INFLUX_EMOJI_MAP = {
    '`OK`': Emoji.SUCCESS,
    '`FAIL`': Emoji.FAILED,
    '`NO_DATA`': Emoji.NO_DATA,
}


class InfluxParams(NamedTuple):
    """Influx params storage"""
    host: str
    port: int
    username: str
    database: str
    metrics: Dict[str, str]


class InfluxSource(Source):
    """InfluxDB client"""

    CONFIG_ID = 'influxdb'
    _params: InfluxParams = None

    @classmethod
    def params(cls) -> InfluxParams:
        if cls._params is None:
            cls._params = InfluxParams(**cls.config.params)
        return cls._params

    def __init__(self, client: Client):
        super().__init__(client, polling_interval=INFLUX_POLLING_INTERVAL)
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
                password=BOT_CONFIG.influx_password,
                database=params.database,
                ssl=True,
                verify_ssl=True)
        return self._influx_client

    @classmethod
    def convert(cls, data: dict) -> str:
        data.pop('From', None)
        text = convert(data)
        text = '*From InfluxDB*\n' + replace_emoji(text, INFLUX_EMOJI_MAP)
        return text.strip()

    async def get_update(self) -> Optional[Json]:
        metrics = self.params().metrics
        results = await asyncio.gather(*[
            self._get_status(met) for met in metrics.values()
        ])
        statuses: Dict[str, str] = dict(zip(
            metrics.keys(),
            results
        ))
        return statuses

    async def _get_status(self, entity):
        query = f'SELECT LAST(*) FROM {entity} LIMIT 1;'
        try:
            last_record = await self.influx_client.query(query)
            last_time = last_record.raw['series'][0]['values'][0][0]
            last_time_ms = _convert_time(last_time)
            now = datetime.utcnow().timestamp()
            if now - last_time_ms < 300:
                return 'OK'
            return 'FAIL'
        except KeyError:
            return 'NO_DATA'


class InfluxTimestampParseException(Exception):
    """Error during Influx timestamp parsing"""


_RE_TIME_GROUPS = re.compile(r'(.+)\.(\d+)(Z)')


def _convert_time(timestamp) -> float:
    match_ts = _RE_TIME_GROUPS.match(timestamp)
    if match_ts is None:
        raise InfluxTimestampParseException
    timestamp, nsec, timezone, *_ = match_ts.groups()
    msec = nsec[:6]
    dtime = datetime.strptime(f'{timestamp}.{msec}{timezone}', '%Y-%m-%dT%H:%M:%S.%fZ')
    return dtime.timestamp()
