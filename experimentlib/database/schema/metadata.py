from __future__ import annotations

import enum
import re
import typing
from datetime import datetime, timezone

import attr


class ConditionError(Exception):
    pass


class Operator(enum.Enum):
    EQUAL = '='
    NOT_EQUAL = '!='

    MATCH = '=~'
    NOT_MATCH = '!~'

    GREATER = '>'
    GREATER_EQUAL = '>='

    LESSER = '<'
    LESSER_EQUAL = '<='


class LogicOperator(enum.Enum):
    AND = 'AND'
    OR = 'OR'


@attr.s(frozen=True)
class Conditional(object):
    left: str = attr.ib()
    right: str = attr.ib()

    operator: typing.Union[Operator, LogicOperator] = attr.ib()

    _REGEX_STR = re.compile(r'^([\w]+)\s*(=|!=|=~|!~|>|>=|<|<=)\s*([\w\d]+)$')

    def __str__(self) -> str:
        if self.operator == Operator.MATCH or self.operator == Operator.NOT_MATCH:
            right_str = f"/{self.right!s}/"
        elif isinstance(self.right, datetime):
            right_str = f"'{self.right.astimezone(timezone.utc).replace(tzinfo=None).isoformat()}Z'"
        elif isinstance(self.right, str):
            right_str = f"'{self.right!s}'"
        else:
            right_str = str(self.right)

        return f"({self.left!s} {self.operator.value} {right_str})"

    def __invert__(self):
        if self.operator == Operator.EQUAL:
            operator_inverted = Operator.NOT_EQUAL
        elif self.operator == Operator.NOT_EQUAL:
            operator_inverted = Operator.EQUAL
        elif self.operator == Operator.MATCH:
            operator_inverted = Operator.NOT_MATCH
        elif self.operator == Operator.NOT_MATCH:
            operator_inverted = Operator.MATCH
        elif self.operator == Operator.GREATER:
            operator_inverted = Operator.LESSER_EQUAL
        elif self.operator == Operator.GREATER_EQUAL:
            operator_inverted = Operator.LESSER
        elif self.operator == Operator.LESSER:
            operator_inverted = Operator.GREATER_EQUAL
        elif self.operator == Operator.LESSER_EQUAL:
            operator_inverted = Operator.GREATER
        else:
            raise ValueError(f"{self.operator} has no inverted counterpart")

        # noinspection PyArgumentList
        return type(self)(self.left, self.right, operator_inverted)

    def __and__(self, other):
        # noinspection PyArgumentList
        return type(self)(self, other, LogicOperator.AND)

    def __or__(self, other):
        # noinspection PyArgumentList
        return type(self)(self, other, LogicOperator.OR)

    @classmethod
    def from_str(cls, x: str) -> Conditional:
        x_match = cls._REGEX_STR.match(x)

        if x_match is None:
            raise ConditionError(f"Input \"{x}\" did not match expected format")

        # noinspection PyArgumentList
        return cls(x_match[1], x_match[3], Operator(x_match[2]))
