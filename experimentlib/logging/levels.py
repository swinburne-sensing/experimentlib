import logging


__all__ = ['NOTSET', 'META', 'LOCK', 'TRACE', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']


# Logging level aliases
NOTSET = logging.NOTSET
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL


# Additional logging levels
logging.META = logging.DEBUG - 3
logging.LOCK = logging.DEBUG - 2
logging.TRACE = logging.DEBUG - 1

logging.addLevelName(logging.META, 'META')
logging.addLevelName(logging.LOCK, 'LOCKS')
logging.addLevelName(logging.TRACE, 'TRACE')

META = logging.META
LOCK = logging.LOCK
TRACE = logging.TRACE
