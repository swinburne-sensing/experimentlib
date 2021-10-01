import collections
import os.path
import re
import typing
from datetime import datetime, tzinfo

from tzlocal import get_localzone

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


def parse_datetime(value: str, parse_tz: typing.Optional[tzinfo] = None) -> datetime:
    """ Date/time or timestamp parser for use with argparse.

    :param value:
    :param parse_tz:
    :return: datetime
    :raises ValueError: on invalid input
    """
    # Default to local datetime
    parse_tz = parse_tz or get_localzone()

    timestamp_match = _REGEX_TIMESTAMP.match(value.lower())

    if timestamp_match is not None:
        timestamp = float(timestamp_match[1])

        if timestamp_match[2] == 'm':
            timestamp /= 1e3
        elif timestamp_match[2] == 'u':
            timestamp /= 1e6
        elif timestamp_match[2] == 'n':
            timestamp /= 1e9

        dt = datetime.fromtimestamp(timestamp)

        return dt.astimezone(parse_tz)
    else:
        dt = None

        for datetime_format in _DATETIME_FORMAT:
            try:
                dt = datetime.strptime(value, datetime_format)
                break
            except ValueError:
                pass

        if dt is not None:
            return dt.astimezone(parse_tz)
        else:
            raise DateTimeParseError(f"\"{value}\" does not match any known datetime format")


def parse_path(value: str) -> str:
    """ Parser for paths, converts relative paths into real paths. Resolves user paths relative to '~'.

    :param value: input str
    :return: real path str
    """
    return os.path.realpath(os.path.expanduser(value))


def parse_pair(value: str, value_separator: typing.Optional[str] = None,
               pair_delimiter: typing.Optional[str] = None, escape: bool = True) -> typing.Mapping[str, str]:
    """ Parse key-value pairs from string input.

    :param value: input str
    :param value_separator: character(s) used to separate keys and values, defaults to '='
    :param pair_delimiter: character(s) used to separate multiple pairs in input str
    :param escape: if True value separator or pair delimiter may be escaped by a preceding '\' in input str
    :return: dict
    """
    value_separator = value_separator or '='

    if pair_delimiter is not None:
        # Split input based on delimiter
        if escape:
            pair_set = re.split(r'(?<!\\)' + pair_delimiter, value)
        else:
            pair_set = value.split(pair_delimiter)

        # Merge recursive call results
        try:
            return dict(collections.ChainMap(*(parse_pair(pair, value_separator, escape=escape) for pair in pair_set)))
        except PairParseError:
            raise PairParseError()

    # Strip spacing and separate
    value = value.strip()

    if escape:
        value_set = re.split(r'(?<!\\)' + value_separator, value)
    else:
        value_set = value.split(value_separator)

    if len(value) == 0 or len(value_set) == 0:
        return {}
    elif len(value_set) == 1:
        raise PairParseError(f"Missing value separator \"{value_separator}\" in pair \"{value}\"")
    elif len(value_set) == 2:
        return {
            value_set[0]: value_set[1]
        }
    else:
        raise PairParseError(f"Multiple value separator \"{value_separator}\" in pair \"{value}\"")
