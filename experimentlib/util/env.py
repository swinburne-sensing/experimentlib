import os
import typing


class EnvironmentVariableError(ValueError):
    pass


def get_variables(prefix: str, cast_bool: typing.Optional[typing.Iterable[str]] = None,
                  cast_float: typing.Optional[typing.Iterable[str]] = None,
                  cast_int: typing.Optional[typing.Iterable[str]] = None,
                  var_ignore: typing.Optional[typing.Iterable[str]] = None) \
        -> typing.Dict[str, typing.Union[bool, float, int, str]]:
    """ Fetch prefixed variables from environment, optionally casting select variable names to bool, float or int.

    :param prefix: environment variable prefix
    :param cast_bool: list of variables to cast to bool
    :param cast_float: list of variables to cast to float
    :param cast_int: list of variables to cast to int
    :param var_ignore: list of variables to discard
    :return: dict of environment variables
    """
    # Get arguments from environment
    env_vars: typing.Dict[str, typing.Union[bool, float, int, str]] = {
        k[len(prefix):].lower(): v for k, v in os.environ.items() if k.startswith(prefix)
    }

    # Discard any ignored variables
    if var_ignore:
        for var_name in var_ignore:
            if var_name in env_vars:
                env_vars.pop(var_name)

    # Cast variables
    if cast_bool:
        for field in cast_bool:
            if field in env_vars:
                try:
                    env_vars[field] = bool(int(env_vars[field]))
                except ValueError as exc:
                    raise EnvironmentVariableError(f"Unable to cast variable \"{prefix}{field.upper()}\" value "
                                                   f"\"{env_vars[field]}\" to boolean") from exc

    if cast_float:
        for field in cast_float:
            if field in env_vars:
                try:
                    env_vars[field] = float(env_vars[field])
                except ValueError as exc:
                    raise EnvironmentVariableError(f"Unable to cast variable \"{prefix}{field.upper()}\" value "
                                                   f"\"{env_vars[field]}\" to float") from exc

    if cast_int:
        for field in cast_int:
            if field in env_vars:
                try:
                    env_vars[field] = int(env_vars[field])
                except ValueError as exc:
                    raise EnvironmentVariableError(f"Unable to cast variable \"{prefix}{field.upper()}\" value "
                                                   f"\"{env_vars[field]}\" to integer") from exc

    return env_vars
