import logging
import typing


T_FILTER_CALLABLE = typing.Callable[[logging.LogRecord], bool]
T_FILTER = typing.Union[logging.Filter, T_FILTER_CALLABLE]


def discard_name_prefix_factory(name: str) -> T_FILTER_CALLABLE:
    """ Filter factory to discard records from loggers with specified prefix.

    :param name: logger name prefix to discard
    :return: logging filter callable
    """
    def f(record: logging.LogRecord) -> bool:
        return not record.name.startswith(name)

    return f


def only_event_factory() -> T_FILTER_CALLABLE:
    """ Filters records based upon the presence and value of the event flag.

    :return: logging filter callable
    """
    def f(record: logging.LogRecord) -> bool:
        return hasattr(record, 'event') and record.event

    return f


def only_notify_factory() -> T_FILTER_CALLABLE:
    """ Filters records based upon the presence and value of the notify flag.

    :return: logging filter callable
    """
    def f(record: logging.LogRecord) -> bool:
        return hasattr(record, 'notify') and record.notify

    return f
