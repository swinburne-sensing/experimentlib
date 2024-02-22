from __future__ import annotations

import collections.abc
import logging
import socket
from enum import IntEnum
from typing import Any, Mapping, MutableMapping, Optional, Union

import urllib3
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import PointSettings

import experimentlib
from experimentlib.logging import levels
from experimentlib.logging.filters import discard_name_prefix_factory
from experimentlib.logging.formatters import InfluxDBFormatter
from experimentlib.util.arg_helper import get_args


class InfluxDBHandlerError(experimentlib.ExperimentLibError):
    pass


class InfluxDBHandler(logging.Handler):
    # HTTP options
    RETRIES = urllib3.Retry(3, redirect=3, backoff_factor=1)

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

    def __init__(self, bucket: Union[str, Mapping[str, str]], name: Optional[str] = None,
                 client_args: Optional[Mapping[str, Any]] = None, level: int = logging.NOTSET,
                 measurement: Optional[str] = None,
                 severity_map: Optional[Mapping[int, Union[int, Severity]]] = None):
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

        name = name or get_args()

        # Force output formatter
        logging.Handler.setFormatter(self, InfluxDBFormatter())

        # Discard records from influxdb_client and urllib3 to prevent recursion
        self.addFilter(discard_name_prefix_factory('influxdb_client.'))
        self.addFilter(discard_name_prefix_factory('urllib3.'))

        self._measurement = measurement or 'syslog'

        # Setup bucket mapping
        self._bucket_map: MutableMapping[int, str] = {}

        if isinstance(bucket, collections.abc.Mapping):
            for bucket_level, bucket_name in bucket.items():
                self._bucket_map[getattr(levels, bucket_level)] = bucket_name
        else:
            self._bucket_map[logging.NOTSET] = str(bucket)

        # Setup severity mapping
        self._severity_map: Mapping[int, InfluxDBHandler.Severity] = {}

        if severity_map is not None:
            for severity_level, severity_obj in severity_map.items():
                if isinstance(severity_obj, int):
                    severity_obj = InfluxDBHandler.Severity(severity_obj)
                
                self._severity_map[severity_level] = severity_obj
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

        health = self._client.health()

        if health.status != 'pass':
            raise InfluxDBHandlerError(f"Health check failed with message: {health.message}")

        self._write_api = self._client.write_api(point_settings=self._point_settings)

    def close(self) -> None:
        super().close()

        # Ensure client is closed on deletion
        if hasattr(self, '_write_api'):
            self._write_api.flush()
            self._write_api.close()

        if hasattr(self, '_client'):
            self._client.close()

    def setFormatter(self, fmt: Optional[logging.Formatter]) -> None:
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
        point.field('severity_code', severity.value)
        point.field('timestamp', record.created)
        point.field('version', 1)

        # Extended fields
        point.field('levelno', record.levelno)
        point.field('lineno', record.lineno)
        point.field('relativeCreated', record.relativeCreated)

        # Syslog compatible tags
        point.tag('severity', severity.keyword)

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
        self._write_api.write(bucket, record=point, write_precision=WritePrecision.NS)
