from __future__ import annotations

import logging
from enum import IntEnum
from json import JSONDecodeError
from typing import Mapping, MutableMapping, Optional, Union, cast

import tenacity
import pushover

from experimentlib.logging.filters import discard_name_prefix_factory
from experimentlib.logging.formatters import PushoverFormatter
from experimentlib.util.arg_helper import get_args


class PushoverHandler(logging.Handler):
    class Priority(IntEnum):
        NO_NOTIFICATION = -2
        QUIET = -1
        DEFAULT = 0
        HIGH = 1
        REQUIRE_CONFIRM = 2

    class _RetryPushoverError(tenacity.retry_base):  # type:ignore[misc, name-defined]
        def __call__(self, retry_state: tenacity.RetryCallState) -> bool:
            exception = retry_state.outcome.exception()  # type:ignore[union-attr]

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

    def __init__(self, api_token: Optional[str], user_key: str, level: int = logging.NOTSET,
                 priority_map: Optional[MutableMapping[int, Union[int, Priority]]] = None,
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
        logging.Handler.setFormatter(self, PushoverFormatter())

        # Discard records from urllib3 to prevent recursion
        self.addFilter(discard_name_prefix_factory('urllib3.'))

        # Parse integers in input mapping
        if priority_map is not None:
            for k, v in priority_map.items():
                if isinstance(v, int):
                    priority_map[k] = PushoverHandler.Priority(v)

        self._priority_map = cast(Mapping[int, PushoverHandler.Priority], priority_map) or self._DEFAULT_PRIORITY_MAP

        # Minimum and maximum supported priority
        self._priority_min = min(self._priority_map.keys())
        self._priority_max = min(self._priority_map.keys())

        self._title = title or get_args()

        # Instantiate client and test connection
        self._client: Optional[pushover.Pushover] = None
        self._user_key = user_key

        if api_token is not None and len(api_token) > 0 and self._user_key is not None and len(self._user_key) > 0:
            self._client = pushover.Pushover(api_token)

        # Verify user key (does not verify API key)
        # self._client.verify()

    def setFormatter(self, fmt: Optional[logging.Formatter]) -> None:
        raise NotImplementedError('Formatter cannot be changed')

    def emit(self, record: logging.LogRecord) -> None:
        if self._client is None:
            # Skip is API token is not configured
            return

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
            self._send_message(msg, priority.value, title, int(record.created), True)
        except pushover.RequestError:
            self.handleError(record)

    
    @tenacity.retry(
        retry=_RetryPushoverError(),
        stop=tenacity.stop_after_delay(600), # type: ignore[attr-defined, no-untyped-call]
        wait=tenacity.wait_fixed(30) # type: ignore[attr-defined, no-untyped-call]
    )
    def _send_message(self, msg: str, priority: int, title: str, timestamp: int, html: bool) -> None:
        if self._client is None:
            # Skip is API token is not configured
            return

        self._client.message(self._user_key, msg, priority=priority, title=title, timestamp=timestamp, html=int(html))
