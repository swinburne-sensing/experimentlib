from __future__ import annotations

import typing
from datetime import datetime, timedelta

import attr
import pandas as pd


@attr.s(frozen=True)
class Series(object):
    query_str: str = attr.ib()

    measurement: str = attr.ib()

    tags: typing.Dict[str, str] = attr.ib()
    data: typing.Union[pd.DataFrame] = attr.ib()

    children: typing.Optional[typing.Sequence[Series]] = attr.ib(default=None)

    start: datetime = attr.ib(init=False)
    end: datetime = attr.ib(init=False)

    duration: timedelta = attr.ib(init=False)

    def __attrs_post_init__(self):
        # Get start, end and duration from data
        object.__setattr__(self, 'start', self.data.index[0])
        object.__setattr__(self, 'end', self.data.index[-1])
        object.__setattr__(self, 'duration', self.end - self.start)

    def __iter__(self):
        yield self

        for child in self.children:
            yield child

    def __str__(self):
        if self.children is not None:
            children = [f"child={child!s}" for child in self.children]
        else:
            children = []

        tag_str = ', '.join(
            [f"{k}={v}" for k, v in self.tags.items()] +
            [
                f"rows={len(self.data)}, cols={len(self.data.columns)}",
                f"duration={self.duration}"
            ] +
            children
        )

        return f"{self.measurement}({tag_str})"

    def update_data(self, data: pd.DataFrame, tags: typing.Optional[typing.Dict[str, str]] = None,
                    children: typing.Optional[typing.Sequence[Series]] = None) -> Series:
        tag_dict = self.tags.copy()

        if tags:
            tag_dict.update(tags)

        return self.__class__(self.query_str, self.measurement, tag_dict, data, children)
