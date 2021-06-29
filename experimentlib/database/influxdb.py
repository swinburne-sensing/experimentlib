import asyncio
import typing

import aioinflux
import pandas as pd
import tzlocal

from experimentlib.database import Series
from experimentlib.logging import classes
from experimentlib.util import async_helper, env


class ClientError(Exception):
    pass


class QueryError(ClientError):
    pass


class ResultError(ClientError):
    pass


class Client(async_helper.HybridSync, classes.LoggedClass):
    def __init__(self, async_enabled: bool = False, async_limit: typing.Optional[int] = None,
                 event_loop: typing.Optional[asyncio.AbstractEventLoop] = None,
                 logger_instance_name: typing.Optional[str] = None, **client_args):
        async_helper.HybridSync.__init__(self, async_enabled, async_limit, event_loop)
        classes.LoggedClass.__init__(self, logger_instance_name)

        self.client = aioinflux.InfluxDBClient(loop=self._async_loop, **client_args)
        self.ping(async_enabled=False)

    @async_helper.HybridSync.wrapper
    async def get_databases(self) -> typing.Sequence[str]:
        db_list = await self._query('SHOW DATABASES')

        return [x[0] for x in db_list['results'][0]['series'][0]['values']]

    @async_helper.HybridSync.wrapper
    async def get_measurements(self, db_name: str) -> typing.Sequence[str]:
        measurement_list = await self._query(f"SHOW MEASUREMENTS ON \"{db_name}\"")

        if 'series' not in measurement_list['results'][0]:
            return []

        return [x[0] for x in measurement_list['results'][0]['series'][0]['values']]

    @async_helper.HybridSync.wrapper
    async def get_retention_policies(self, db_name: str) \
            -> typing.Sequence[str]:
        rp_list = await self._query(f"SHOW RETENTION POLICIES ON \"{db_name}\"")

        return [x[0] for x in rp_list['results'][0]['series'][0]['values']]

    @async_helper.HybridSync.wrapper
    async def ping(self):
        return await self.client.ping()

    async def _query(self, query_str: str):
        self.logger().info(f"Query: \"{query_str}\"")

        try:
            return await self.client.query(query_str)
        except Exception as exc:
            raise QueryError(f"Exception generated from query \"{query_str}\"") from exc

    @async_helper.HybridSync.wrapper
    async def query(self, query_str: str):
        return await self._query(query_str)

    @async_helper.HybridSync.wrapper
    async def query_series(self, query_str: str) -> typing.Sequence[Series]:
        series_list = []

        result_full = await self._query(query_str)

        # Drill down to data
        if 'results' not in result_full:
            raise ResultError('No results in response')

        result = result_full['results']

        if len(result) != 1:
            raise ResultError(f"Expected 1 set of results, got {len(result)}")

        result = result[0]

        if 'series' not in result:
            raise ResultError('No series in response')

        for series in result['series']:
            data = pd.DataFrame(series['values'], columns=series['columns'])

            # Convert time column to datetime
            data.time = pd.to_datetime(data.time)
            data.time = data.time.dt.tz_localize('UTC').dt.tz_convert(tzlocal.get_localzone())

            # Set date as table index
            data = data.set_index('time')

            series_list.append(
                Series(
                    query_str,
                    series['name'],
                    series['tags'],
                    data
                )
            )

        return series_list

    @classmethod
    def from_env(cls, env_prefix: str):
        """

        :param env_prefix:
        :return:
        """
        kwargs = env.get_variables(env_prefix,
                                   cast_bool=('ssl', 'verify_ssl', 'use_udp', 'gzip'),
                                   cast_float=('timeout',),
                                   cast_int=('async_limit', 'port', 'retries', 'udp_port', 'pool_size'))

        return cls(**kwargs)
