from __future__ import annotations

import collections
import logging
import socket
from enum import IntEnum
from typing import Any, Mapping, MutableMapping, Optional, Union

import urllib3
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import ASYNCHRONOUS, PointSettings

from experimentlib.logging import levels
from experimentlib.logging.filters import discard_name_prefix_factory
from experimentlib.logging.formatters import InfluxDBFormatter


class InfluxDBHandler(logging.Handler):
    # HTTP options
    RETRIES = urllib3.Retry(redirect=3, backoff_factor=1)

    # Log keywords (syslog compatible)
    FACILITY_CODE = 14
    FACILITY = 'console'

    # Map logging levels to syslog severity levels
    class Severity(IntEnum):
        EMERGENCY = 0
        ALERT = 1
        CRITICAL = 2
        ERROR = 3
        WARNING = 4
        NOTICE = 5
        INFORMATIONAL = 6
        DEBUG = 7

        @property
        def keyword(self) -> str:
            if self == self.EMERGENCY:
                return 'emerg'
            elif self == self.ALERT:
                return 'alert'
            elif self == self.CRITICAL:
                return 'crit'
            elif self == self.ERROR:
                return 'err'
            elif self == self.WARNING:
                return 'warning'
            elif self == self.NOTICE:
                return 'notice'
            elif self == self.INFORMATIONAL:
                return 'info'
            else:
                return 'debug'

    _DEFAULT_SEVERITY_MAP: Mapping[int, InfluxDBHandler.Severity] = {
        logging.DEBUG: Severity.DEBUG,
        logging.INFO: Severity.INFORMATIONAL,
        logging.WARNING: Severity.WARNING,
        logging.ERROR: Severity.ERROR,
        logging.CRITICAL: Severity.CRITICAL
    }

    def __init__(self, name: str, bucket: Union[str, Mapping[int, str]],
                 client_args: Optional[Mapping[str, Any]] = None, level: int = logging.NOTSET,
                 measurement: Optional[str] = None,
                 severity_map: Mapping[int, Union[int, Severity]] = None):
        """ Sends logs to an InfluxDB instance in a format compatible with InfluxDBs log view. Can be configured to
        alter severity levels and send different log levels to specific buckets, allowing culling of old records.

        :param name: application name to append to logs
        :param bucket: target bucket or mapping of log levels to buckets
        :param client_args:
        :param level: minimum logging level
        :param measurement: measurement name, defaults to 'syslog'
        :param severity_map:
        """
        logging.Handler.__init__(self, level)

        # Force output formatter
        logging.Handler.setFormatter(self, InfluxDBFormatter())

        # Discard records from urllib3 to prevent recursion
        self.addFilter(discard_name_prefix_factory('urllib3.'))

        self._measurement = measurement or 'syslog'

        # Setup bucket mapping
        self._bucket_map: MutableMapping[int, str] = {}

        if isinstance(bucket, collections.Mapping):
            for k, v in bucket.items():
                self._bucket_map[getattr(levels, k)] = v
        else:
            self._bucket_map[logging.NOTSET] = str(bucket)

        # Setup severity mapping
        self._severity_map: MutableMapping[int, InfluxDBHandler.Severity] = {}

        if severity_map is not None:
            for k, v in severity_map.items():
                if isinstance(v, int):
                    self._severity_map[k] = InfluxDBHandler.Severity(v)
        else:
            self._severity_map = self._DEFAULT_SEVERITY_MAP

        self._bucket_min = min(self._bucket_map.keys())
        self._bucket_max = max(self._bucket_map.keys())

        # Create tags common to all records
        self._point_settings = PointSettings(
            appname=name,
            facility=self.FACILITY,
            host=socket.gethostname(),
            hostname=socket.getfqdn()
        )

        # Instantiate client and test connection
        if client_args is None:
            self._client = InfluxDBClient.from_env_properties()
        else:
            self._client = InfluxDBClient(**client_args, retries=self.RETRIES)

    def __del__(self):
        # Ensure client is closed on deletion
        if hasattr(self, '_client') and self._client is not None:
            self._client.close()

    def setFormatter(self, fmt: logging.Formatter) -> None:
        raise NotImplementedError('InfluxDB formatter cannot be changed, hard-coded to match syslog format')

    def emit(self, record: logging.LogRecord) -> None:
        # Determine closest mappable severity level
        severity_level = record.levelno

        if severity_level not in self._severity_map:
            severity_level = min(self._severity_map.keys(), key=lambda x: abs(x - severity_level))

        severity = self._severity_map[severity_level]

        # Find closest bucket in map
        bucket = self._bucket_map[min(self._bucket_map.keys(), key=lambda x: abs(x - record.levelno))]

        point = Point(self._measurement)

        # Syslog compatible fields
        point.field('facility_code', self.FACILITY_CODE)
        point.field('message', self.format(record))
        point.field('procid', record.process or 0)
        point.field('severity_code', severity.keyword)
        point.field('timestamp', record.created)
        point.field('version', 1)

        # Extended fields
        point.field('levelno', record.levelno)
        point.field('lineno', record.lineno)
        point.field('relativeCreated', record.relativeCreated)

        # Syslog compatible tags
        point.tag('severity', severity.value)

        # Extended tags
        point.tag('name', record.name)
        point.tag('filename', record.filename)
        point.tag('funcName', record.funcName or '')
        point.tag('levelname', record.levelname)
        point.tag('module', record.module)
        point.tag('pathname', record.pathname)
        point.tag('processName', record.processName or '')
        point.tag('threadName', record.threadName or '')

        # Write point
        with self._client.write_api(ASYNCHRONOUS, self._point_settings) as write_api:
            write_api.write(bucket, record=point, write_precision=WritePrecision.NS)
