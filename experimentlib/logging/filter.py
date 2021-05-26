import logging


def filter_event(record: logging.LogRecord) -> bool:
    """ Filters records based upon the presence and value of the event flag.

    :param record: Record from Logger
    :return: bool
    """
    return hasattr(record, 'event') and record.event


def filter_notify(record: logging.LogRecord) -> bool:
    """ Filters records based upon the presence and value of the notify flag.

    :param record: Record from Logger
    :return: bool
    """
    return hasattr(record, 'notify') and record.notify
