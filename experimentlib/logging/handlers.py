from __future__ import annotations

import atexit
import enum
import json
import logging
import logging.handlers
import queue as queue_lib
import re
import socket
import sys
import time
import typing

# noinspection PyUnresolvedReferences
from logging.config import ConvertingDict, ConvertingList, valid_ident

import colorama
import influxdb
import pushover
import ratelimit
import tenacity

from . import filters, formatters, levels


def _resolve_converting_dict(convert_dict: ConvertingDict) -> typing.Dict:
    # Check for cached conversion result
    if '__resolved__' in convert_dict:
        return convert_dict['__resolved__']

    # Get class and constructor
    init_class = convert_dict.configurator.resolve(convert_dict.pop('class'))

    props = convert_dict.pop('.', None)
    kwargs = {key: convert_dict[key] for key in convert_dict if valid_ident(key)}

    instance = init_class(**kwargs)

    if props:
        for name, value in props.items():
            setattr(instance, name, value)

    # Cache instance
    convert_dict['__resolved__'] = instance

    return instance


def _resolve_converting_list(convert_list: ConvertingList) -> typing.List:
    return [convert_list[i] for i in range(len(convert_list))]


class BufferedHandler(logging.Handler):
    """ Log buffer, useful for presentation of records in a user interface while discarding messages beyond a limit or
    after a specified time.
    """

    def __init__(self, level: int = logging.NOTSET, record_limit: typing.Optional[int] = None,
                 record_timeout: typing.Optional[float] = None):
        """

        :param level:
        :param record_limit:
        :param record_timeout:
        """
        super(BufferedHandler, self).__init__(level)

        self._record_limit = record_limit
        self._record_timeout = record_timeout

        self._record_buffer: typing.List[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        # Discard old records
        self._update()

        # Append record to buffer
        self._record_buffer.append(record)

    @property
    def records(self) -> typing.FrozenSet[logging.LogRecord]:
        # Discard old records
        self._update()

        return frozenset(self._record_buffer)

    def _update(self):
        """ Discard records beyond the configured record count limit and/or configures record timeout.
        """
        if self._record_limit:
            while len(self._record_buffer) > self._record_limit:
                self._record_buffer.pop(0)

        if self._record_timeout:
            expiry = time.time() - self._record_timeout

            while len(self._record_buffer) > 0:
                if self._record_buffer[0].created < expiry:
                    self._record_buffer.pop(0)


class ColoramaStreamHandler(logging.StreamHandler):
    """ Colourised stream handler. """
    color_map: typing.Optional[typing.Mapping[int, int]] = {
        levels.META: colorama.Fore.LIGHTBLUE_EX,
        levels.LOCK: colorama.Style.BRIGHT + colorama.Fore.LIGHTBLACK_EX,
        levels.TRACE: colorama.Style.BRIGHT + colorama.Fore.LIGHTBLACK_EX,
        logging.DEBUG: colorama.Style.RESET_ALL,
        logging.INFO: colorama.Fore.GREEN,
        logging.WARNING: colorama.Style.BRIGHT + colorama.Fore.YELLOW,
        logging.ERROR: colorama.Style.BRIGHT + colorama.Fore.RED,
        logging.CRITICAL: colorama.Back.RED + colorama.Fore.BLACK
    }

    __RE_TRACEBACK = re.compile(r'^[a-z._]+: ', re.IGNORECASE)

    def __init__(self, stream: typing.Optional[typing.IO] = None,
                 color_map: typing.Optional[typing.Dict[int, int]] = None):
        stream = stream or sys.stdout

        super().__init__(colorama.AnsiToWin32(stream).stream)

        if color_map is not None:
            self.color_map = color_map

    @property
    def is_tty(self):
        # Check if stream is outputting to interactive session
        isatty = getattr(self.stream, 'isatty', None)

        return isatty and isatty()

    def format(self, record):
        message = super().format(record)

        if self.is_tty:
            message = '\n'.join((self.colorize(line, record) for line in message.split('\n')))

        return message

    def colorize(self, message: str, record: logging.LogRecord):
        try:
            return f"{self.color_map[record.levelno]}{message}{colorama.Style.RESET_ALL}"
        except KeyError:
            return message


class InfluxDBHandler(logging.Handler):
    # Log keywords (syslog compatible)
    FACILITY_CODE = 14
    FACILITY = 'console'

    class Severity(enum.IntEnum):
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

    # Map logging levels to syslog severity levels
    _DEFAULT_SEVERITY_MAP: typing.Mapping[int, InfluxDBHandler.Severity] = {
        logging.DEBUG: Severity.DEBUG,
        logging.INFO: Severity.INFORMATIONAL,
        logging.WARNING: Severity.WARNING,
        logging.ERROR: Severity.ERROR,
        logging.CRITICAL: Severity.CRITICAL
    }

    def __init__(self, name: str, level: int = logging.NOTSET,
                 client_args: typing.Optional[typing.Mapping[str, typing.Any]] = None, measurement: str = 'syslog',
                 severity_map: typing.Dict[int, typing.Union[int, Severity]] = None):
        """

        :param name:
        :param client_args:
        :param severity_map:
        :param level:
        """
        # Discard records from urllib3 to prevent recursion
        super(InfluxDBHandler, self).__init__(level)

        # Discard records from urllib3 to prevent recursion
        self.addFilter(filters.discard_name_prefix_factory('urllib3.'))

        # Force formatter
        self.setFormatter(formatters.InfluxDBFormatter())

        self._measurement = measurement

        # Parse integers in input mapping
        if severity_map is not None:
            for k, v in severity_map.items():
                if isinstance(v, int):
                    severity_map[k] = InfluxDBHandler.Severity(v)

        self._severity_map = severity_map or self._DEFAULT_SEVERITY_MAP

        # Minimum and maximum supported priority
        self._severity_min = min(self._severity_map.keys())
        self._severity_max = min(self._severity_map.keys())

        # Create shared tags dict
        self._tags = {
            'appname': name,
            'facility': self.FACILITY,
            'host': socket.gethostname(),
            'hostname': socket.getfqdn(),
        }

        # Instantiate client and test connection
        client_args = client_args or {}
        self._client = influxdb.InfluxDBClient(**client_args)

        self._client.ping()

    def emit(self, record: logging.LogRecord) -> None:
        # Determine closest mappable severity level
        level = record.levelno

        if level not in self._severity_map:
            level = min(self._severity_map.keys(), key=lambda x: abs(x - level))

        severity = self._severity_map[level]

        payload = {
            'measurement': self._measurement,
            'fields': {
                # Syslog compatible fields
                'facility_code': self.FACILITY_CODE,
                'message': self.format(record),
                'procid': record.process or 0,
                'severity_code': severity.keyword,
                'timestamp': record.created,
                'version': 1,

                # Extended fields
                'levelno': record.levelno,
                'lineno': record.lineno,
                'relativeCreated': record.relativeCreated
            },
            'tags': {
                # Syslog compatible tags
                'severity': severity.value,

                # Extended tags
                'name': record.name,
                'filename': record.filename,
                'funcName': record.funcName or '',
                'levelname': record.levelname,
                'module': record.module,
                'pathname': record.pathname,
                'processName': record.processName or '',
                'threadName': record.threadName or ''
            },
            'time': int(record.created * 1e9)
        }

        # Append shared tags
        payload['tags'].update(self._tags)

        self._client.write_points([payload], 'n')


class PushoverHandler(logging.Handler):
    class Priority(enum.IntEnum):
        NO_NOTIFICATION = -2
        QUIET = -1
        DEFAULT = 0
        HIGH = 1
        REQUIRE_CONFIRM = 2

    class _RetryPushoverError(tenacity.retry_base):
        def __call__(self, retry_state: tenacity.RetryCallState) -> bool:
            exception = retry_state.outcome.exception()

            # Retry on connection or protocol errors
            if any((isinstance(exception, t) for t in (ConnectionError, json.JSONDecodeError))):
                return True

            if isinstance(exception, pushover.RequestError):
                if 'application token' in exception.errors:
                    # Invalid API key, do not retry
                    return False
                elif 'user key' in exception.errors:
                    # Invalid user key, do not retry
                    return False
                else:
                    # Unknown error
                    return False

            # Otherwise do not retry
            return False

    # Map logging levels to Pushover priority levels
    _DEFAULT_PRIORITY_MAP: typing.Mapping[int, PushoverHandler.Priority] = {
        logging.DEBUG: Priority.NO_NOTIFICATION,
        logging.INFO: Priority.QUIET,
        logging.WARNING: Priority.DEFAULT,
        logging.ERROR: Priority.HIGH,
        logging.CRITICAL: Priority.HIGH
    }

    def __init__(self, level: int = logging.NOTSET,
                 client_args: typing.Optional[typing.Mapping[str, typing.Any]] = None,
                 priority_map: typing.Dict[int, typing.Union[int, Priority]] = None,
                 title: typing.Optional[str] = None):
        """

        :param client_args:
        :param priority_map:
        :param title:
        :param level:
        """
        super(PushoverHandler, self).__init__(level)

        # Discard records from urllib3 to prevent recursion
        self.addFilter(filters.discard_name_prefix_factory('urllib3.'))

        # Force formatter
        self.setFormatter(formatters.PushoverFormatter())

        # Parse integers in input mapping
        if priority_map is not None:
            for k, v in priority_map.items():
                if isinstance(v, int):
                    priority_map[k] = PushoverHandler.Priority(v)

        self._priority_map = priority_map or self._DEFAULT_PRIORITY_MAP

        # Minimum and maximum supported priority
        self._priority_min = min(self._priority_map.keys())
        self._priority_max = min(self._priority_map.keys())

        self._title = title

        # Instantiate client and test connection
        client_args = client_args or {}
        self._client = pushover.Client(**client_args)

        # Verify user key (does not verify API key)
        # self._client.verify()

    def emit(self, record: logging.LogRecord) -> None:
        # Format record
        msg = self.format(record)

        # Determine closest mappable priority level
        level = record.levelno

        if level not in self._priority_map:
            level = min(self._priority_map.keys(), key=lambda x: abs(x - level))

        title = self._title or record.name
        priority = self._priority_map[level]

        # Send message to Pushover client (with retrying and rate limiting)
        try:
            self._send_message(msg, priority.value, title, record.created, True)
        except pushover.RequestError:
            self.handleError(record)

    @tenacity.retry(retry=_RetryPushoverError(), stop=tenacity.stop_after_delay(600),
                    wait=tenacity.wait_fixed(30))
    @ratelimit.sleep_and_retry
    @ratelimit.limits(calls=1, period=2)
    def _send_message(self, msg: str, priority: int, title: str, timestamp: int, html: bool):
        self._client.send_message(msg, priority=priority, title=title, timestamp=timestamp, html=int(html))


_T_QUEUE = typing.Union[queue_lib.SimpleQueue[typing.Any], queue_lib.Queue[typing.Any], ConvertingDict]
_T_HANDLERS = typing.Union[typing.Iterable[logging.Handler], ConvertingList]


class QueueListenerHandler(logging.handlers.QueueHandler):
    def __init__(self, handlers: _T_HANDLERS, queue: typing.Optional[_T_QUEUE] = None, queue_size: int = -1,
                 auto_start: bool = True, respect_handler_level: bool = True) -> None:
        if isinstance(queue, ConvertingDict):
            queue = _resolve_converting_dict(queue)
        elif not queue:
            queue = queue_lib.Queue(queue_size)

        if isinstance(handlers, ConvertingList):
            handlers = _resolve_converting_list(handlers)

        super().__init__(queue)

        # Create listener thread
        # noinspection PyUnresolvedReferences
        self._listener = logging.handlers.QueueListener(self.queue, *handlers,
                                                        respect_handler_level=respect_handler_level)

        if auto_start:
            self.start()

            # Stop listener on exit
            atexit.register(self.stop)

    def start(self):
        self._listener.start()

    def stop(self):
        self._listener.stop()
