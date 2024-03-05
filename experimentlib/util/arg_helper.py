from __future__ import annotations

import collections
import os.path
import re
import sys
import typing
from datetime import datetime, tzinfo
from types import SimpleNamespace
from typing import Any, Callable, Optional, MutableMapping, Sequence, Union

import attr
from tzlocal import get_localzone

from .constant import FORMAT_DATE, FORMAT_TIMESTAMP_FILENAME, FORMAT_TIMESTAMP_CONSOLE


_DATETIME_FORMAT = [
    FORMAT_TIMESTAMP_CONSOLE,
    FORMAT_TIMESTAMP_FILENAME,
    FORMAT_DATE
]

_REGEX_TIMESTAMP = re.compile(r'^([\d]+\.?[\d]*)([smun]?)$')

_ARG_DELIMITER = ':'
_LIST_DELIMITER = ','
_VALUE_DELIMITER = '='


class ArgumentError(ValueError):
    pass


class DateTimeParseError(ValueError):
    pass


class PairParseError(ValueError):
    pass


class SimpleArgParser(object):
    @attr.s(frozen=True)
    class _SimpleArg(object):
        name: str = attr.ib()
        default: Any = attr.ib()
        converter: Optional[Callable[[str], Any]] = attr.ib()
        validator: Optional[Callable[[str], Any]] = attr.ib()
        values: Optional[Sequence[Any]] = attr.ib()
        greedy: bool = attr.ib()
        required: bool = attr.ib()

        def parse(self, arg_str: str) -> Any:
            if self.converter is not None:
                arg_value = self.converter(arg_str)
            else:
                arg_value = arg_str

            if self.validator is not None:
                if not self.validator(arg_value):
                    raise ArgumentError(f"Value \"{arg_value}\" not valid for argument {self.name}")

            if self.values is not None:
                if arg_value not in self.values:
                    raise ArgumentError(f"Value \"{arg_value}\" for valid for argument {self.name} (allowed: "
                                        f"{', '.join(self.values)})")

            return arg_value

    def __init__(self, arg_delimiter: Optional[str] = None, list_delimiter: Optional[str] = None):
        """

        :param arg_delimiter:
        :param list_delimiter:
        """
        self._arg_delimiter = arg_delimiter or _ARG_DELIMITER
        self._list_delimiter = list_delimiter or _LIST_DELIMITER

        self._arg_parser_mapping: typing.OrderedDict[str, SimpleArgParser._SimpleArg] = collections.OrderedDict()

    @staticmethod
    def _macro_lower(x: str) -> str:
        return x.lower()

    @staticmethod
    def _macro_upper(x: str) -> str:
        return x.upper()

    def add_argument(self, name: str, default: Optional[Any] = None,
                     converter: Union[None, str, Callable[[str], Any]] = None,
                     validator: Optional[Callable[[Any], bool]] = None, values: Optional[Sequence[Any]] = None,
                     greedy: bool = False, required: bool = True) -> None:
        """

        :param name:
        :param default:
        :param converter:
        :param validator:
        :param values:
        :param greedy:
        :param required:
        :return:
        """
        if isinstance(converter, str):
            converter = converter.lower()

            if converter == 'lower':
                converter = self._macro_lower
            elif converter == 'upper':
                converter = self._macro_upper
            else:
                raise ArgumentError(f"Unrecognised converter macro {converter}")

        if any(arg.greedy for arg in self._arg_parser_mapping.values()):
            raise ArgumentError('Cannot add arguments when greedy argument already in list')

        self._arg_parser_mapping[name] = self._SimpleArg(name, default, converter, validator, values, greedy, required)

    def parse(self, arg_str: str) -> SimpleNamespace:
        """

        :param arg_str:
        :return:
        """
        arg_namespace = {}
        arg_split = re.split(self._list_delimiter + '''(?=(?:[^'"]|'[^']*'|"[^"]*")*$)''', arg_str)

        # Tracking for positional arguments
        arg_parser_mapping = self._arg_parser_mapping.copy()
        arg_pos = True

        for arg_n, arg_value in enumerate(arg_split):
            if self._arg_delimiter in arg_value:
                # Split name and value
                arg_name, arg_value = arg_value.split(self._arg_delimiter, 1)
                arg_name = arg_name.strip().lower()

                if arg_name in arg_namespace:
                    raise ArgumentError(f"Duplicate argument \"{arg_name}\" in \"{arg_str}\"")

                if arg_name not in arg_parser_mapping:
                    raise ArgumentError(f"Unknown argument \"{arg_name}\" in \"{arg_str}\"")

                arg_parser = arg_parser_mapping.pop(arg_name)

                # No additional positional arguments allowed
                arg_pos = False
            else:
                if not arg_pos:
                    raise ArgumentError(f"Positional argument used after keyword argument in \"{arg_str}\"")

                if len(arg_parser_mapping) == 0:
                    raise ArgumentError(f"Unmatched argument name \"{arg_str}\"")

                arg_name, arg_parser = arg_parser_mapping.popitem(False)

            if arg_parser.greedy:
                arg_namespace[arg_name] = [arg_parser.parse(x.strip()) for x in [arg_value] + arg_split[arg_n + 1:]]
                break

            arg_namespace[arg_name] = arg_parser.parse(arg_value.strip())

        # Add any remaining argument defaults
        for arg_parser in arg_parser_mapping.values():
            if arg_parser.required:
                raise ArgumentError(f"Argument {arg_parser.name} must be provided")

            arg_namespace[arg_parser.name] = arg_parser.default

        return SimpleNamespace(**arg_namespace)


def get_args() -> str:
    return ' '.join(sys.argv)


def parse_datetime(value: str, parse_tz: Optional[tzinfo] = None) -> datetime:
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


def parse_pair(value: str, value_separator: Optional[str] = None,
               list_delimiter: Optional[str] = None, escape: bool = True) -> MutableMapping[str, str]:
    """ Parse key-value pairs from string input.

    :param value: input str
    :param value_separator: character(s) used to separate keys and values, defaults to '='
    :param list_delimiter: character(s) used to separate multiple pairs in input str
    :param escape: if True value separator or pair delimiter may be escaped by a preceding '\' in input str
    :return: dict
    """
    value_separator = value_separator or _VALUE_DELIMITER

    if list_delimiter is not None:
        # Split input based on delimiter
        if escape:
            pair_set = re.split(r'(?<!\\)' + list_delimiter, value)
        else:
            pair_set = value.split(list_delimiter)

        # Merge recursive call results
        try:
            return dict(
                collections.ChainMap(
                    *(parse_pair(pair, value_separator, escape=escape) for pair in pair_set)
                )
            )
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
