import os.path
import re
import typing
from datetime import datetime

from .constant import FORMAT_DATE, FORMAT_TIMESTAMP_FILENAME, FORMAT_TIMESTAMP_CONSOLE


_DATETIME_FORMAT = [
    FORMAT_TIMESTAMP_CONSOLE,
    FORMAT_TIMESTAMP_FILENAME,
    FORMAT_DATE
]

_REGEX_TIMESTAMP = re.compile(r'^([\d]+\.?[\d]*)([smun]?)$')

_PAIR_DELIMIETER = '='


class DateTimeParseError(ValueError):
    pass


class PairParseError(ValueError):
    pass


def parse_datetime(value: str) -> datetime:
    """ Date/time or timestamp parser for use with argparse.

    :param value:
    :return: datetime
    :raises ValueError: on invalid input
    """
    timestamp_match = _REGEX_TIMESTAMP.match(value.lower())

    if timestamp_match is not None:
        timestamp = float(timestamp_match[1])

        if timestamp_match[2] == 'm':
            timestamp /= 1e3
        elif timestamp_match[2] == 'u':
            timestamp /= 1e6
        elif timestamp_match[2] == 'n':
            timestamp /= 1e9

        return datetime.fromtimestamp(timestamp)
    else:
        dt = None

        for datetime_format in _DATETIME_FORMAT:
            try:
                dt = datetime.strptime(value, datetime_format)
                break
            except ValueError:
                pass

        if dt is not None:
            return dt
        else:
            raise DateTimeParseError(f"\"{value}\" does not match any known datetime format")


def parse_path(value: str) -> str:
    return os.path.realpath(value)


def parse_pair(value: str) -> typing.Optional[typing.Dict[str, str]]:
    # Strip comments
    if '#' in value:
        value = value[:value.find('#')]

    # Strip spacing and seperate
    value = value.strip()
    value_set = value.split(_PAIR_DELIMIETER)

    if len(value) == 0 or len(value_set) == 0:
        return None
    elif len(value_set) == 1:
        raise PairParseError(f"Missing delimieter character \"{_PAIR_DELIMIETER}\" in input \"{value}\"")
    elif len(value_set) == 2:
        return {
            value_set[0]: value_set[1]
        }
    else:
        raise PairParseError(f"Multiple delimieter characters \"{_PAIR_DELIMIETER}\" in input \"{value}\"")
