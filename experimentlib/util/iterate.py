import typing
from itertools import tee


TValue = typing.TypeVar('TValue')


def flatten_list(iterable: typing.Iterable[typing.Any]) -> typing.Iterable[typing.Any]:
    for item in iterable:
        if isinstance(item, list) or isinstance(item, tuple) or isinstance(item, set):
            for sub_item in flatten_list(item):
                yield sub_item
        else:
            yield item


def iterate_chunk(data: typing.Sequence[TValue], size: int) -> typing.Generator[typing.Sequence[TValue], None, None]:
    """ Get iterator to return portions of a sequence in chunks of a maximum size.

    :param data: input sequence
    :param size: maximum chunk size
    :return: iterator
    """
    for n in range(0, len(data), size):
        yield data[n:n + size]


def iterate_pair(data: typing.Iterable[TValue]) -> typing.Iterable[typing.Tuple[TValue, TValue]]:
    """ Get iterator to return pairs of elements from an iterable.

    :param data: input iterator
    :return: iterator
    """
    iter_a, iter_b = tee(data)
    next(iter_b, None)
    return zip(iter_a, iter_b)
