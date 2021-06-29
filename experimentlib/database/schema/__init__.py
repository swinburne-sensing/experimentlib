import typing

from experimentlib.data import unit


T_VALUE = typing.Union[None, str, int, float, unit.Quantity]

__all__ = ['T_VALUE']
