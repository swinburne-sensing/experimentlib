from __future__ import annotations
import getpass
import os.path
import socket
import tempfile
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Iterable, Mapping, Optional, TextIO, Union

import yaml

from experimentlib.data import unit
from experimentlib.logging import classes
from experimentlib.util import arg_helper, classes as util_classes, constant, time as elib_time


class ExtendedError(yaml.YAMLError):  # type: ignore[misc]
    """ Base class for errors generated via the extended YAML loader. """
    pass


class ConstructorError(ExtendedError):
    """ Base class for errors generated during construction of custom nodes. Includes additional information about the
    location of the error. """
    def __init__(self, msg: str, node: Optional[yaml.ScalarNode] = None, include_node: bool = True):
        if node is not None:
            if node.start_mark.name == '<unicode string>':
                source = node.start_mark.name
            else:
                source = f"\"{os.path.realpath(node.start_mark.name)}\""
        else:
            source = '<unknown>'

        # Append node data to exception message
        if include_node:
            msg = msg.strip() + f" from YAML node \"{node.tag}\": \"{node.value}\" from {source}, line " \
                            f"{node.start_mark.line + 1}"
        else:
            msg = msg.strip() + f" from {source}, line {node.start_mark.line + 1}"

        super().__init__(msg)


class EnvironmentTagError(ConstructorError):
    pass


class FormatTagError(ConstructorError):
    pass


class IncludeTagError(ConstructorError):
    pass


class ResolveTagError(ConstructorError):
    pass


class ExtendedLoader(classes.Logged, yaml.SafeLoader):  # type: ignore[misc]
    """ An extended YAML loader including additional tags and security features. """

    # Shared mapping for format constructor (environment and system variables)
    _format_mapping_system: Mapping[str, str] = {
        'user_path': os.path.expanduser('~'),
        'temp_path': tempfile.gettempdir(),
        'system_hostname': socket.getfqdn(),
        'system_username': getpass.getuser(),
        **{'env_' + env_var: env_val for env_var, env_val in os.environ.items()}
    }

    def __init__(self, stream: Union[str, TextIO], enable_resolve: bool = False,
                 include_paths: Optional[Iterable[str]] = None,
                 format_kwargs: Optional[Mapping[str, str]] = None):
        self._stream_root: Optional[str]
        stream_filename: str

        if isinstance(stream, TextIO):
            self._stream_root, stream_filename = os.path.split(stream.name)
        else:
            self._stream_root = None
            stream_filename = '<str>'

        classes.Logged.__init__(self, f"src:{stream_filename}")
        yaml.SafeLoader.__init__(self, stream)

        # Flag to allow resolving of objects
        self._enable_resolve = enable_resolve

        # Restricted paths for include tag
        self._include_paths = []

        if include_paths:
            for path in include_paths:
                path = os.path.realpath(os.path.expanduser(path))

                if not os.path.isdir(path):
                    raise ExtendedError(f"Include path \"{path}\" not a directory")

                self._include_paths.append(path)
                self.logger().debug(f"Include allowed from \"{path}\"")

        # Additional format kwargs
        self._format_kwargs = format_kwargs

    def _format_str(self, format_str: str) -> str:
        """ Format specified string with system and environment variables.

        :param format_str: formatted string specification
        :return: formatted string
        :raises IndexError: on invalid format specification
        :raises KeyError: on format specification with unknown field codes
        """
        timestamp = elib_time.now()
        timestamp_utc = timestamp.astimezone(timezone.utc)

        format_mapping = {
            'date': timestamp.strftime(constant.FORMAT_DATE),
            'date_utc': timestamp_utc.strftime(constant.FORMAT_DATE),
            'time': timestamp.strftime(constant.FORMAT_TIME),
            'time_utc': timestamp_utc.strftime(constant.FORMAT_TIME),
            'datetime': timestamp.strftime(constant.FORMAT_TIMESTAMP_FILENAME),
            'datetime_utc': timestamp_utc.strftime(constant.FORMAT_TIMESTAMP_FILENAME),
            'datetime_iso': timestamp.isoformat(),
            'datetime_utc_iso': timestamp_utc.isoformat(),
            'timestamp': str(int(timestamp.timestamp()))
        }

        format_mapping.update(self._format_mapping_system)

        if self._format_kwargs is not None:
            format_mapping.update(self._format_kwargs)

        return format_str.format(**format_mapping)

    def _format_node(self, node: yaml.ScalarNode) -> str:
        """

        :param node: YAML node
        :return:
        """
        try:
            return self._format_str(node.value)
        except IndexError:
            raise FormatTagError('Invalid field format', node)
        except KeyError as exc:
            raise FormatTagError(f"Format field \"{exc!s}\" not found", node) from None
        except Exception as exc:
            raise FormatTagError('Unhandled exception', node) from exc

    @staticmethod
    def construct_datetime(_: Any, node: yaml.ScalarNode) -> datetime:
        """ Construct datetime from node string.

        :param _: unused
        :param node: YAML node
        :return: datetime
        """
        return arg_helper.parse_datetime(node.value)

    @staticmethod
    def construct_datetime_utc(_: Any, node: yaml.ScalarNode) -> datetime:
        """ Construct datetime from node string.

        :param _: unused
        :param node: YAML node
        :return: datetime
        """
        return arg_helper.parse_datetime(node.value, timezone.utc)

    @staticmethod
    def construct_env(_: Any, node: yaml.ScalarNode) -> Optional[str]:
        """ Construct string from environment variable specified in node.

        :param _: unused
        :param node: YAML node
        :return: environment variable content as string or None
        """
        node = node.value.split(' ', 1)

        if node[0] not in os.environ:
            if len(node) == 1:
                # Return nothing when no default is provided
                return None
            elif len(node) == 2:
                return str(node[1])
            else:
                raise EnvironmentTagError('Tag should only contain variable name and default value', node)

        return os.environ[node[0]]

    @staticmethod
    def construct_env_required(_: Any, node: yaml.ScalarNode) -> str:
        """ Construct string from environment variable specified in node.

        :param _: unused
        :param node: YAML node
        :return: environment variable content as string
        :raises EnvironmentTagError: on undefined environment variable
        """
        if node.value not in os.environ:
            raise EnvironmentTagError(f"Environment variable \"{node.value}\" not defined", node)

        return os.environ[node.value]

    def construct_format(self, node: yaml.ScalarNode) -> str:
        """ Construct formatted string from node.

        :param node: YAML node
        :return: formatted string
        """
        return self._format_node(node)

    def construct_include(self, node: yaml.ScalarNode) -> Any:
        """ Include content from another YAML file, optionally limiting the paths of files that can be included.

        Inspired by: https://stackoverflow.com/questions/528281/how-can-i-include-an-yaml-file-inside-another

        :param node: YAML node
        :return: any structure supported by YAML
        """
        if self._stream_root is None:
            raise ConstructorError('Include tag cannot be used when parsing input string', node)

        include_path_real = None

        for include_path in node.value.split(';'):
            include_path_formatted = self._format_str(os.path.expanduser(include_path))

            # Check for relative path
            if not include_path_formatted.startswith('/') and not include_path_formatted.startswith('\\'):
                include_path_formatted = os.path.join(self._stream_root, include_path_formatted)

            include_path_real = os.path.realpath(include_path_formatted)

            if os.path.isfile(include_path_real):
                self.logger().debug(f"Including: {include_path_real}")
                break
            else:
                self.logger().debug(f"File not found: {include_path_real}")

        if include_path_real is None:
            raise IncludeTagError('No valid filename in include tag', node)

        if len(self._include_paths) > 0:
            if not any((include_path_real.startswith(path) for path in self._include_paths)):
                raise IncludeTagError(f"Included file \"{include_path_real}\" not within restricted include path", node,
                                      include_node=False)

        with open(include_path_real) as f:
            # Include from specified path, inheriting restricted paths
            include_data = yaml.load(f, ExtendedLoader.factory(self._enable_resolve, self._include_paths,
                                                               self._format_kwargs))

            return include_data

    def construct_resolve(self, node: yaml.ScalarNode) -> Any:
        """ Resolve tag to Python object from global scope.

        :param node:
        :return: anything
        """
        if not self._enable_resolve:
            raise ResolveTagError('Resolve tags not enabled', node)

        try:
            return util_classes.resolve_global(node.value)
        except Exception as exc:
            raise ResolveTagError('Exception thrown while resolving node', node) from exc

    @staticmethod
    def construct_timedelta(_: Any, node: yaml.ScalarNode) -> timedelta:
        node_unit = unit.parse(node.value)

        node_seconds = node_unit.m_as(unit.registry.sec)

        return timedelta(seconds=node_seconds)

    @classmethod
    def factory(cls, *args: Any, **kwargs: Any) -> Callable[..., ExtendedLoader]:
        """ Get a wrapped constructor for ExtendedLoader with include paths restricted to the specified paths.

        :param args: passed to constructor
        :param kwargs: passed to constructor
        :return: wrapped constructor
        """
        def f(stream: Union[str, TextIO]) -> ExtendedLoader:
            return cls(stream, *args, **kwargs)

        return f


# Add constructors
ExtendedLoader.add_constructor('!datetime', ExtendedLoader.construct_datetime)
ExtendedLoader.add_constructor('!datetime_utc', ExtendedLoader.construct_datetime_utc)
ExtendedLoader.add_constructor('!envreq', ExtendedLoader.construct_env_required)
ExtendedLoader.add_constructor('!env', ExtendedLoader.construct_env)
ExtendedLoader.add_constructor('!format', ExtendedLoader.construct_format)
ExtendedLoader.add_constructor('!include', ExtendedLoader.construct_include)
ExtendedLoader.add_constructor('!resolve', ExtendedLoader.construct_resolve)
ExtendedLoader.add_constructor('!timedelta', ExtendedLoader.construct_timedelta)


def load(stream: Union[str, TextIO], *args: Any, **kwargs: Any) -> Any:
    """ Equivalent to yaml.load using the extended loader

    :param stream: input string or stream object for parsing
    :param args:
    :param kwargs:
    :return:
    """
    return yaml.load(stream, ExtendedLoader.factory(*args, **kwargs))
