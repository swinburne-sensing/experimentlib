import os
import typing


class EnvironmentVariableError(ValueError):
    pass


def get_variables(prefix: str, cast_bool: typing.Optional[typing.Iterable[str]] = None,
                  cast_float: typing.Optional[typing.Iterable[str]] = None,
                  cast_int: typing.Optional[typing.Iterable[str]] = None) -> typing.Dict[str, typing.Union[bool, float,
                                                                                                           int, str]]:
    # Get arguments from environment
    client_args = {k[len(prefix):].lower(): v for k, v in os.environ.items() if
                   k.startswith(prefix)}

    # Cast variables
    if cast_bool:
        for field in cast_bool:
            if field in client_args:
                try:
                    client_args[field] = bool(int(client_args[field]))
                except ValueError as exc:
                    raise EnvironmentVariableError(f"Unable to cast variable \"{prefix}{field.upper()}\" value "
                                                   f"\"{client_args[field]}\" to boolean") from exc

    if cast_float:
        for field in cast_float:
            if field in client_args:
                try:
                    client_args[field] = float(client_args[field])
                except ValueError as exc:
                    raise EnvironmentVariableError(f"Unable to cast variable \"{prefix}{field.upper()}\" value "
                                                   f"\"{client_args[field]}\" to float") from exc

    if cast_int:
        for field in cast_int:
            if field in client_args:
                try:
                    client_args[field] = int(client_args[field])
                except ValueError as exc:
                    raise EnvironmentVariableError(f"Unable to cast variable \"{prefix}{field.upper()}\" value "
                                                   f"\"{client_args[field]}\" to integer") from exc

    return client_args
