import getpass
import os.path
import socket
import tempfile
import time
import typing

import yaml

import experimentlib.logging.classes as classes
import experimentlib.util.constant as constant


class ExtendedError(yaml.YAMLError):
    """ Base class for errors generated via the extended YAML loader. """
    pass


class ConstructorError(ExtendedError):
    """ Base class for errors generated during construction of custom nodes. Includes additional information about the
    location of the error. """
    def __init__(self, msg: str, node: typing.Optional[yaml.ScalarNode] = None, include_node: bool = True):
        if node.start_mark.name == '<unicode string>':
            source = node.start_mark.name
        else:
            source = f"\"{os.path.realpath(node.start_mark.name)}\""

        # Append node data to exception message
        if include_node:
            msg = msg.strip() + f" in node \"{node.tag}\": \"{node.value}\" from {source}, line " \
                            f"{node.start_mark.line}"
        else:
            msg = msg.strip() + f" from {source}, line {node.start_mark.line}"

        super(ExtendedError, self).__init__(msg)


class EnvironmentTagError(ConstructorError):
    pass


class FormatTagError(ConstructorError):
    pass


class IncludeTagError(ConstructorError):
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

    def __init__(self, stream: typing.Union[str, typing.IO],
                 include_paths: typing.Optional[typing.Iterable[str]] = None):
        if type(stream) is not str:
            self._stream_root = os.path.split(stream.name)[0]
        else:
            self._stream_root = None

        classes.LoggedClass.__init__(self)
        yaml.SafeLoader.__init__(self, stream)

        # Restricted paths for include tag
        self._include_paths = []

        if include_paths:
            for path in include_paths:
                path = os.path.realpath(os.path.expanduser(path))

                if not os.path.isdir(path):
                    raise ExtendedError(f"Include path \"{path}\" not a directory")

                self._include_paths.append(path)

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
    def construct_env_required(_, node: yaml.ScalarNode) -> str:
        """ Construct string from environment variable specified in node.

        :param _: unused
        :param node: YAML node
        :return: environment variable content as string
        :raises EnvironmentTagError: on undefined environment variable
        """
        if node.value not in os.environ:
            raise EnvironmentTagError(f"\"{node.value}\" not defined")

        return os.environ[node.value]

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
                raise EnvironmentTagError('Tag should only contain variable name and default value')

        return os.environ[node[0]]

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
            raise ConstructorError('Include tag cannot be used when parsing strings')

        include_path_abs = None

        for include_path in node.value.split(';'):
            include_path_formatted = self._format_str(os.path.expanduser(include_path))

            # Check for relative path
            if not include_path_formatted.startswith('/') and not include_path_formatted.startswith('\\'):
                include_path_formatted = os.path.join(self._stream_root, include_path_formatted)

            include_path_abs = os.path.realpath(include_path_formatted)

            if os.path.isfile(include_path_abs):
                self.logger().info(f"Including: {include_path_abs}")
                break
            else:
                self.logger().debug(f"File not found: {include_path_abs}")

        if include_path_abs is None:
            raise IncludeTagError('No valid filename in include tag', node)

        if self._include_paths is not None:
            if not any((include_path_abs.startswith(path) for path in self._include_paths)):
                raise IncludeTagError(f"Included file \"{include_path_abs}\" not within restricted include path", node,
                                      include_node=False)

        with open(include_path_abs) as f:
            # Include from specified path, inheriting restricted paths
            include_data = yaml.load(f, ExtendedLoader.factory(self._include_paths))

            return include_data

    @classmethod
    def factory(cls, include_paths: typing.Iterable[str]):
        """ Get a wrapped constructor for ExtendedLoader with include paths restricted to the specified paths.

        :param include_paths: list of paths from which files may be included from
        :return: wrapped constructor
        """
        def f(stream):
            return cls(stream, include_paths)

        return f


# Add constructors
ExtendedLoader.add_constructor('!envreq', ExtendedLoader.construct_env_required)
ExtendedLoader.add_constructor('!env', ExtendedLoader.construct_env)
ExtendedLoader.add_constructor('!format', ExtendedLoader.construct_format)
ExtendedLoader.add_constructor('!include', ExtendedLoader.construct_include)
