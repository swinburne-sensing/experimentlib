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
setattr(logging, 'META', logging.NOTSET + 1)
# Logging lock acquisition/release
setattr(logging, 'LOCK', logging.DEBUG - 2)
# Logging for detailed debugging
setattr(logging, 'TRACE', logging.DEBUG - 1)
# Logging external I/O
setattr(logging, 'COMM', logging.DEBUG + 1)

# noinspection PyUnresolvedReferences
logging.addLevelName(logging.META, 'META')  # type: ignore[attr-defined]
logging.addLevelName(logging.LOCK, 'LOCKS')  # type: ignore[attr-defined]
logging.addLevelName(logging.TRACE, 'TRACE')  # type: ignore[attr-defined]
logging.addLevelName(logging.COMM, 'COMM')  # type: ignore[attr-defined]

META = logging.META  # type: ignore[attr-defined]
LOCK = logging.LOCK  # type: ignore[attr-defined]
TRACE = logging.TRACE  # type: ignore[attr-defined]
COMM = logging.COMM  # type: ignore[attr-defined]

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
