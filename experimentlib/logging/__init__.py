import logging
import logging.config
import typing

from experimentlib.logging.handlers import ColoramaStreamHandler
from experimentlib.logging.levels import *


# Loggers the generate lots of messages, can sometimes be useful to suppress output to provide cleaner logs
_SUPPRESSED_LOGGERS = [
    'aioinflux',
    'matplotlib.font_manager',
    'pymodbus',
    'pyvisa',
    'transitions.core',
    'urllib3',
    'urllib3.connectionpool'
]


class ExtendedLogger(logging.Logger):
    """ Extended logger class with additional logging levels and support for useful filtering arguments. """
    @staticmethod
    def _update_kwargs(notify: bool, event: bool, kwargs_dict):
        """ Takes boolean arguments for notify and event and places them within the 'extra' key passed to Logger class
        methods.

        :param notify: if True this message should be marked as a notification
        :param event: if True this message should be marked as an event
        :param kwargs_dict: dict of keyword arguments passed to Logger methods
        """
        if 'extra' not in kwargs_dict:
            kwargs_dict['extra'] = {}

        if notify:
            kwargs_dict['extra'].update({'notify': True})
        else:
            kwargs_dict['extra'].update({'notify': False})

        if event:
            kwargs_dict['extra'].update({'event': True})
        else:
            kwargs_dict['extra'].update({'event': False})

    def log(self, level: int, msg: str, *args, notify: bool = False, event: bool = False, **kwargs):
        """ og 'msg % args' with specified level.

        :param level: log severity level
        :param msg: log message
        :param args: message and additional arguments passed to _log
        :param notify: True when this log should be forwarded to a user, False otherwise
        :param event: True when this log should be recorded as an event, False otherwise
        :param kwargs: additional keyword arguments passed to _log
        :return:
        """
        if self.isEnabledFor(level):
            self._log(level, msg, args, **kwargs)

    def comm(self, msg: str, *args, notify: bool = False, event: bool = False, **kwargs):
        """ Log 'msg % args' with severity 'COMM'.

        Useful for low-level communication logging, such as to external hardware.

        :param msg: log message
        :param args: message and additional arguments passed to _log
        :param notify: True when this log should be forwarded to a user, False otherwise
        :param event: True when this log should be recorded as an event, False otherwise
        :param kwargs: additional keyword arguments passed to _log
        """
        if self.isEnabledFor(COMM):
            self._update_kwargs(notify, event, kwargs)
            self._log(COMM, msg, args, **kwargs)

    def trace(self, msg: str, *args, notify: bool = False, event: bool = False, **kwargs):
        """ Log 'msg % args' with severity 'TRACE'.

        Useful for low-level tracing, more detailed that typical debug messages.

        :param msg: log message
        :param args: message and additional arguments passed to _log
        :param notify: True when this log should be forwarded to a user, False otherwise
        :param event: True when this log should be recorded as an event, False otherwise
        :param kwargs: additional keyword arguments passed to _log
        """
        if self.isEnabledFor(TRACE):
            self._update_kwargs(notify, event, kwargs)
            self._log(TRACE, msg, args, **kwargs)

    def lock(self, msg: str, *args, notify: bool = False, event: bool = False, **kwargs):
        """ Log 'msg % args' with severity 'LOCK'.

        Useful for tracking lock/release state of shared objects.

        :param msg: log message
        :param args: message and additional arguments passed to _log
        :param notify: True when this log should be forwarded to a user, False otherwise
        :param event: True when this log should be recorded as an event, False otherwise
        :param kwargs: additional keyword arguments passed to _log
        """
        if self.isEnabledFor(LOCK):
            self._update_kwargs(notify, event, kwargs)
            self._log(LOCK, msg, args, **kwargs)

    def meta(self, msg: str, *args, notify: bool = False, event: bool = False, **kwargs):
        """ Log 'msg % args' with severity 'META'.

        Useful for logging about logging (eg. creation or destruction of logger objects).

        :param msg: log message
        :param args: message and additional arguments passed to _log
        :param notify: True when this log should be forwarded to a user, False otherwise
        :param event: True when this log should be recorded as an event, False otherwise
        :param kwargs: additional keyword arguments passed to _log
        """
        if self.isEnabledFor(META):
            self._update_kwargs(notify, event, kwargs)
            self._log(META, msg, args, **kwargs)

    def debug(self, msg: str, *args, notify: bool = False, event: bool = False, **kwargs):
        if self.isEnabledFor(DEBUG):
            self._update_kwargs(notify, event, kwargs)
            self._log(DEBUG, msg, args, **kwargs)

    def info(self, msg: str, *args, notify: bool = False, event: bool = False, **kwargs):
        if self.isEnabledFor(INFO):
            self._update_kwargs(notify, event, kwargs)
            self._log(INFO, msg, args, **kwargs)

    def warning(self, msg: str, *args, notify: bool = True, event: bool = False, **kwargs):
        if self.isEnabledFor(WARNING):
            self._update_kwargs(notify, event, kwargs)
            self._log(WARNING, msg, args, **kwargs)

    def error(self, msg: str, *args, notify: bool = True, event: bool = True, **kwargs):
        if self.isEnabledFor(ERROR):
            self._update_kwargs(notify, event, kwargs)
            self._log(ERROR, msg, args, **kwargs)

    def exception(self, msg: str, *args, notify: bool = True, event: bool = True, exc_info: bool = True, **kwargs):
        if self.isEnabledFor(ERROR):
            self._update_kwargs(notify, event, kwargs)
            self._log(ERROR, msg, args, exc_info=exc_info, **kwargs)

    def critical(self, msg: str, *args, notify: bool = True, event: bool = True, **kwargs):
        if self.isEnabledFor(CRITICAL):
            self._update_kwargs(notify, event, kwargs)
            self._log(CRITICAL, msg, args, **kwargs)


# Replace base logging class with extended version
logging.setLoggerClass(ExtendedLogger)


def get_logger(name: typing.Optional[str] = None) -> ExtendedLogger:
    """ Wrapper for standard getLogger method.

    :param name: name of logger, otherwise root logger is returned
    :return: derived Logger
    """
    logger = logging.getLogger(name)
    logger = typing.cast(ExtendedLogger, logger)

    # Ensure logger is enabled
    logger.disabled = False

    return logger


def basic_logging(suppress_suggested: bool = True, include_thread: bool = False, include_process: bool = False,
                  **kwargs):
    """ Wrapper for standard basic logging that uses a colourised console stream by default.

    :param suppress_suggested: if True some recommended loggers will be raised to the INFO level to reduce log spam
    :param include_thread:
    :param include_process:
    :param kwargs: keyword arguments passed to logging.basicConfig
    """
    if 'handlers' not in kwargs:
        kwargs['handlers'] = [ColoramaStreamHandler()]

    if 'format' not in kwargs:
        kwargs['format'] = (
            '%(asctime)s.%(msecs)03d [%(levelname).1s] ' +
            ('%(processName)s:' if include_process else '') +
            ('%(threadName)s:' if include_thread else '') +
            '%(name)s: %(message)s'
        )

    if 'datefmt' not in kwargs:
        kwargs['datefmt'] = '%y%m%d %H:%M:%S'

    if 'filename' in kwargs:
        # Manually add to handlers list
        kwargs['handlers'].append(logging.FileHandler(kwargs.pop('filename'), encoding='utf-8'))

    if 'level' in kwargs and type(kwargs['level']) is str:
        # Convert string to level number, supports additional levels without modding logging.basicConfig
        kwargs['level'] = NAME_TO_LEVEL[kwargs['level'].upper()]

    logging.basicConfig(**kwargs)

    if suppress_suggested:
        for logger_name in _SUPPRESSED_LOGGERS:
            logging.getLogger(logger_name).setLevel(INFO)


def dict_config(config: typing.Dict[str, typing.Any]) -> None:
    """ Wrapper for standard dictionary configured logging.

    :param config: configuration dictionary
    """
    logging.config.dictConfig(config)


def shutdown(*args, **kwargs):
    """ Shortcut to logging.shutdown.
    
    :param args: passed to logging.shutdown
    :param kwargs:  passed to logging.shutdown
    """
    logging.shutdown(*args, **kwargs)
