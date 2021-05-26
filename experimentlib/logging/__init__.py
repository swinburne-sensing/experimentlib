import logging
import typing


# Additional logging levels
logging.META = logging.DEBUG - 3
logging.LOCK = logging.DEBUG - 2
logging.TRACE = logging.DEBUG - 1

# Additional logging levels
logging.addLevelName(logging.META, 'META')
logging.addLevelName(logging.LOCK, 'LOCKS')
logging.addLevelName(logging.TRACE, 'TRACE')

# Logging level aliases
NOTSET = logging.NOTSET
META = logging.META
LOCK = logging.LOCK
TRACE = logging.TRACE
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL


class ExtendedLogger(logging.Logger):
    """ Extended logger class with additional logging levels and support for useful filtering arguments. """
    @staticmethod
    def _update_args(notify: bool, event: bool, kwargs_dict):
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

    def log(self, level, msg, *args, notify: bool = False, event: bool = False, **kwargs):
        self._update_args(notify, event, kwargs)

        super(ExtendedLogger, self).log(level, msg, *args, **kwargs)

    def trace(self, *args, notify: bool = False, event: bool = False, **kwargs):
        """ Log

        :param args:
        :param notify:
        :param event:
        :param kwargs:
        :return:
        """
        self._update_args(notify, event, kwargs)

        if self.isEnabledFor(TRACE):
            self.log(TRACE, *args, **kwargs)

    def lock(self, *args, notify: bool = False, event: bool = False, **kwargs):
        """

        :param args:
        :param notify:
        :param event:
        :param kwargs:
        :return:
        """
        self._update_args(notify, event, kwargs)

        if self.isEnabledFor(LOCK):
            self.log(LOCK, *args, **kwargs)

    def meta(self, *args, notify: bool = False, event: bool = False, **kwargs):
        """

        :param args:
        :param notify:
        :param event:
        :param kwargs:
        :return:
        """
        self._update_args(notify, event, kwargs)

        if self.isEnabledFor(META):
            self.log(META, *args, **kwargs)

    def debug(self, msg, *args, notify: bool = False, event: bool = False, **kwargs):
        self._update_args(notify, event, kwargs)
        super(ExtendedLogger, self).debug(msg, *args, **kwargs)

    def info(self, msg, *args, notify: bool = False, event: bool = False, **kwargs):
        self._update_args(notify, event, kwargs)
        super(ExtendedLogger, self).info(msg, *args, **kwargs)

    def warning(self, msg, *args, notify: bool = True, event: bool = False, **kwargs):
        self._update_args(notify, event, kwargs)
        super(ExtendedLogger, self).warning(msg, *args, **kwargs)

    def error(self, msg, *args, notify: bool = True, event: bool = True, **kwargs):
        self._update_args(notify, event, kwargs)
        super(ExtendedLogger, self).error(msg, *args, **kwargs)

    def exception(self, msg, *args, notify: bool = True, event: bool = True, exc_info: bool = True, **kwargs):
        self._update_args(notify, event, kwargs)
        super(ExtendedLogger, self).exception(msg, *args, exc_info=exc_info, **kwargs)

    def critical(self, msg, *args, notify: bool = True, event: bool = True, **kwargs):
        self._update_args(notify, event, kwargs)
        super(ExtendedLogger, self).critical(msg, *args, **kwargs)


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
