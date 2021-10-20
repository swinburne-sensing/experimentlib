from typing import Any, Iterable, Sequence
from itertools import tee


def flatten_list(iterable: Iterable[Any]):
    for item in iterable:
        if isinstance(item, list) or isinstance(item, tuple) or isinstance(item, set):
            for sub_item in flatten_list(item):
                yield sub_item
        else:
            yield item


def iterate_chunk(data: Sequence[Any], size: int):
    """ Get iterator to return portions of a sequence in chunks of a maximum size.

    :param data: input sequence
    :param size: maximum chunk size
    :return: iterator
    """
    for n in range(0, len(data), size):
        yield data[n:n + size]


def iterate_pair(data: Iterable[Any]):
    """ Get iterator to return pairs of elements from an iterable.

    :param data: input iterator
    :return: iterator
    """
    iter_a, iter_b = tee(data)
    next(iter_b, None)
    return zip(iter_a, iter_b)
