from __future__ import annotations

import logging
from enum import IntEnum
from json import JSONDecodeError
from typing import Mapping, MutableMapping, Optional, Union

import tenacity
import pushover

from experimentlib.logging.filters import discard_name_prefix_factory
from experimentlib.logging.formatters import PushoverFormatter


class PushoverHandler(logging.Handler):
    class Priority(IntEnum):
        NO_NOTIFICATION = -2
        QUIET = -1
        DEFAULT = 0
        HIGH = 1
        REQUIRE_CONFIRM = 2

    class _RetryPushoverError(tenacity.retry_base):
        def __call__(self, retry_state: tenacity.RetryCallState) -> bool:
            exception = retry_state.outcome.exception()

            # Retry on connection or protocol errors
            if any((isinstance(exception, t) for t in (ConnectionError, JSONDecodeError))):
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
    _DEFAULT_PRIORITY_MAP: Mapping[int, PushoverHandler.Priority] = {
        logging.DEBUG: Priority.NO_NOTIFICATION,
        logging.INFO: Priority.QUIET,
        logging.WARNING: Priority.DEFAULT,
        logging.ERROR: Priority.HIGH,
        logging.CRITICAL: Priority.HIGH
    }

    def __init__(self, api_token: str, user_key: str, level: int = logging.NOTSET,
                 priority_map: MutableMapping[int, Union[int, Priority]] = None,
                 title: Optional[str] = None):
        """

        :param api_token:
        :param user_key:
        :param level:
        :param priority_map:
        :param title:
        """
        logging.Handler.__init__(self, level)

        # Force formatter
        self.setFormatter(PushoverFormatter())

        # Discard records from urllib3 to prevent recursion
        self.addFilter(discard_name_prefix_factory('urllib3.'))

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
        self._client = pushover.Pushover(api_token)
        self._user_key = user_key

        # Verify user key (does not verify API key)
        # self._client.verify()

    def setFormatter(self, fmt: logging.Formatter) -> None:
        raise NotImplementedError('Formatter cannot be changed')

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
    def _send_message(self, msg: str, priority: int, title: str, timestamp: int, html: bool):
        self._client.message(self._user_key, msg, priority=priority, title=title, timestamp=timestamp, html=int(html))
