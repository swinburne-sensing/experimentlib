import getpass
import os.path
import socket
import tempfile
import time
import typing
from datetime import datetime, timedelta, timezone

import yaml

from experimentlib.data import unit
from experimentlib.logging import classes
from experimentlib.util import arg_helper, classes as util_classes, constant


class ExtendedError(yaml.YAMLError):
    """ Base class for errors generated via the extended YAML loader. """
    pass


class ConstructorError(ExtendedError):
    """ Base class for errors generated during construction of custom nodes. Includes additional information about the
    location of the error. """
    def __init__(self, msg: str, node: typing.Optional[yaml.ScalarNode] = None, include_node: bool = True):
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

        ExtendedError.__init__(self, msg)


class EnvironmentTagError(ConstructorError):
    pass


class FormatTagError(ConstructorError):
    pass


class IncludeTagError(ConstructorError):
    pass


class ResolveTagError(ConstructorError):
    pass


class ExtendedLoader(classes.LoggedClass, yaml.SafeLoader):
    """ An extended YAML loader including additional tags and security features. """

    # Shared mapping for format constructor (environment and system variables)
    _format_mapping_system = {
        'path_user': os.path.expanduser('~'),
        'path_temp': tempfile.gettempdir(),
        'system_hostname': socket.getfqdn(),
        'system_username': getpass.getuser(),
        **{'env_' + env_var: env_val for env_var, env_val in os.environ.items()}
    }

    def __init__(self, stream: typing.Union[str, typing.IO], enable_resolve: bool = False,
                 include_paths: typing.Optional[typing.Iterable[str]] = None):
        if type(stream) is not str:
            self._stream_root, stream_filename = os.path.split(stream.name)
        else:
            self._stream_root = None
            stream_filename = '<str>'

        classes.LoggedClass.__init__(self, f"src:{stream_filename}")
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

    @classmethod
    def _format_str(cls, format_str: str) -> str:
        """ Format specified string with system and environment variables.

        :param format_str: formatted string specification
        :return: formatted string
        :raises IndexError: on invalid format specification
        :raises KeyError: on format specification with unknown field codes
        """
        format_mapping = {
            'date': time.strftime(constant.FORMAT_DATE),
            'time': time.strftime(constant.FORMAT_TIME),
            'datetime': time.strftime(constant.FORMAT_TIMESTAMP_FILENAME),
            'timestamp': str(int(time.time()))
        }

        format_mapping.update(cls._format_mapping_system)

        return format_str.format(**format_mapping)

    @classmethod
    def _format_node(cls, node: yaml.ScalarNode):
        """

        :param node: YAML node
        :return:
        """
        try:
            return cls._format_str(node.value)
        except IndexError:
            raise FormatTagError('Invalid field format', node)
        except KeyError as exc:
            raise FormatTagError(f"Format field \"{exc!s}\" not found", node) from None
        except Exception as exc:
            raise FormatTagError('Unhandled exception', node) from exc

    @staticmethod
    def construct_datetime(_, node: yaml.ScalarNode) -> datetime:
        """ Construct datetime from node string.

        :param _: unused
        :param node: YAML node
        :return: datetime
        """
        return arg_helper.parse_datetime(node.value)

    @staticmethod
    def construct_datetime_utc(_, node: yaml.ScalarNode) -> datetime:
        """ Construct datetime from node string.

        :param _: unused
        :param node: YAML node
        :return: datetime
        """
        return arg_helper.parse_datetime(node.value, timezone.utc)

    @staticmethod
    def construct_env(_, node: yaml.ScalarNode) -> typing.Optional[str]:
        """ Construct string from environment variable specified in node.

        :param _: unused
        :param node: YAML node
        :return: environment variable content as string or None
        """
        node = node.value.split(' ', 1)

        if node[0] not in os.environ:
            if len(node) == 1:
                return None
            elif len(node) == 2:
                return node[1]
            else:
                raise EnvironmentTagError('Tag should only contain variable name and default value', node)

        return os.environ[node[0]]

    @staticmethod
    def construct_env_required(_, node: yaml.ScalarNode) -> str:
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

    def construct_include(self, node: yaml.ScalarNode) -> typing.Any:
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
                self.logger().info(f"Including: {include_path_real}")
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
            include_data = yaml.load(f, ExtendedLoader.factory(self._enable_resolve, self._include_paths))

            return include_data

    def construct_resolve(self, node: yaml.ScalarNode) -> typing.Any:
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
    def construct_timedelta(_, node) -> timedelta:
        node_unit = unit.parse(node.value)

        node_seconds = node_unit.m_as(unit.registry.sec)

        return timedelta(seconds=node_seconds)

    @classmethod
    def factory(cls, enable_resolve: bool = False, include_paths: typing.Optional[typing.Iterable[str]] = None):
        """ Get a wrapped constructor for ExtendedLoader with include paths restricted to the specified paths.

        :param enable_resolve:
        :param include_paths: list of paths from which files may be included from
        :return: wrapped constructor
        """
        def f(stream):
            return cls(stream, enable_resolve, include_paths)

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


# Wrapper for yaml.load using the extended loader
def load(stream: typing.Union[str, typing.IO], *args, **kwargs):
    return yaml.load(stream, ExtendedLoader.factory(*args, **kwargs))
