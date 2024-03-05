import logging
import logging.config
import typing

from experimentlib.logging.handlers.console import ColoramaStreamHandler
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

    def log(self, level: int, msg: object, *args: object, notify: bool = False, event: bool = False, **kwargs: typing.Any) -> None:
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
            if 'extra' not in kwargs:
                kwargs['extra'] = {}

            if notify:
                kwargs['extra'].update({'notify': True})
            else:
                kwargs['extra'].update({'notify': False})

            if event:
                kwargs['extra'].update({'event': True})
            else:
                kwargs['extra'].update({'event': False})
            
            super().log(level, msg, *args, **kwargs)

    def comm(self, msg: object, *args: object, notify: bool = False, event: bool = False, **kwargs: typing.Any) -> None:
        """ Log 'msg % args' with severity 'COMM'.

        Useful for low-level communication logging, such as to external hardware.

        :param msg: log message
        :param args: message and additional arguments passed to _log
        :param notify: True when this log should be forwarded to a user, False otherwise
        :param event: True when this log should be recorded as an event, False otherwise
        :param kwargs: additional keyword arguments passed to _log
        """
        self.log(COMM, msg, *args, notify=notify, event=event, **kwargs)

    def trace(self, msg: object, *args: object, notify: bool = False, event: bool = False, **kwargs: typing.Any) -> None:
        """ Log 'msg % args' with severity 'TRACE'.

        Useful for low-level tracing, more detailed that typical debug messages.

        :param msg: log message
        :param args: message and additional arguments passed to _log
        :param notify: True when this log should be forwarded to a user, False otherwise
        :param event: True when this log should be recorded as an event, False otherwise
        :param kwargs: additional keyword arguments passed to _log
        """
        self.log(TRACE, msg, *args, notify=notify, event=event, **kwargs)

    def lock(self, msg: object, *args: object, notify: bool = False, event: bool = False, **kwargs: typing.Any) -> None:
        """ Log 'msg % args' with severity 'LOCK'.

        Useful for tracking lock/release state of shared objects.

        :param msg: log message
        :param args: message and additional arguments passed to _log
        :param notify: True when this log should be forwarded to a user, False otherwise
        :param event: True when this log should be recorded as an event, False otherwise
        :param kwargs: additional keyword arguments passed to _log
        """
        self.log(LOCK, msg, *args, notify=notify, event=event, **kwargs)

    def meta(self, msg: object, *args: object, notify: bool = False, event: bool = False, **kwargs: typing.Any) -> None:
        """ Log 'msg % args' with severity 'META'.

        Useful for logging about logging (eg. creation or destruction of logger objects).

        :param msg: log message
        :param args: message and additional arguments passed to _log
        :param notify: True when this log should be forwarded to a user, False otherwise
        :param event: True when this log should be recorded as an event, False otherwise
        :param kwargs: additional keyword arguments passed to _log
        """
        self.log(META, msg, *args, notify=notify, event=event, **kwargs)

    def debug(self, msg: object, *args: object, notify: bool = False, event: bool = False, **kwargs: typing.Any) -> None:
        self.log(DEBUG, msg, *args, notify=notify, event=event, **kwargs)

    def info(self, msg: object, *args: object, notify: bool = False, event: bool = False, **kwargs: typing.Any) -> None:
        self.log(INFO, msg, *args, notify=notify, event=event, **kwargs)

    def warning(self, msg: object, *args: object, notify: bool = False, event: bool = False, **kwargs: typing.Any) -> None:
        self.log(WARNING, msg, *args, notify=notify, event=event, **kwargs)

    def error(self, msg: object, *args: object, notify: bool = True, event: bool = True, **kwargs: typing.Any) -> None:
        self.log(ERROR, msg, *args, notify=notify, event=event, **kwargs)

    def exception(self, msg: object, *args: object, **kwargs: typing.Any) -> None:
        self.log(ERROR, msg, *args, notify=True, event=True, exc_info=True, **kwargs)

    def critical(self, msg: object, *args: object, notify: bool = True, event: bool = True, **kwargs: typing.Any) -> None:
        self.log(CRITICAL, msg, *args, notify=notify, event=event, **kwargs)


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


def basic_logging(filename: typing.Optional[str] = None, suppress_suggested: bool = True, include_thread: bool = False,
                  include_process: bool = False, **kwargs: typing.Any) -> None:
    """ Wrapper for standard basic logging that uses a colourised console stream by default.

    :param filename:
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

    if filename is not None:
        # Manually add to handlers list
        kwargs['handlers'].append(logging.FileHandler(filename, encoding='utf-8'))

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


def shutdown(*args: typing.Any, **kwargs: typing.Any) -> None:
    """ Shortcut to logging.shutdown.

    :param args: passed to logging.shutdown
    :param kwargs:  passed to logging.shutdown
    """
    logging.shutdown(*args, **kwargs)
