import logging


__all__ = ['NOTSET', 'META', 'LOCK', 'TRACE', 'DEBUG', 'COMM', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', 'NAME_TO_LEVEL']


# Logging level aliases
NOTSET = logging.NOTSET
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL


# Additional logging levels
# Logging about logging
logging.META = logging.NOTSET + 1
# Logging lock acquisition/release
logging.LOCK = logging.DEBUG - 2
# Logging for detailed debugging
logging.TRACE = logging.DEBUG - 1
# Logging external I/O
logging.COMM = logging.DEBUG + 1

# noinspection PyUnresolvedReferences
logging.addLevelName(logging.META, 'META')
# noinspection PyUnresolvedReferences
logging.addLevelName(logging.LOCK, 'LOCKS')
# noinspection PyUnresolvedReferences
logging.addLevelName(logging.TRACE, 'TRACE')
# noinspection PyUnresolvedReferences
logging.addLevelName(logging.COMM, 'COMM')

# noinspection PyUnresolvedReferences
META = logging.META
# noinspection PyUnresolvedReferences
LOCK = logging.LOCK
# noinspection PyUnresolvedReferences
TRACE = logging.TRACE
# noinspection PyUnresolvedReferences
COMM = logging.COMM


NAME_TO_LEVEL = {
    'NOTSET': NOTSET,
    'META': META,
    'LOCK': LOCK,
    'TRACE': TRACE,
    'DEBUG': DEBUG,
    'COMM': COMM,
    'INFO': INFO,
    'WARNING': WARNING,
    'WARN': WARNING,
    'ERROR': ERROR,
    'CRITICAL': CRITICAL,
    'FATAL': CRITICAL
}
