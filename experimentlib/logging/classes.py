import abc
import typing

from experimentlib import logging as elib_logging
from experimentlib.util import classes


class LoggedMetaclass(abc.ABCMeta):
    """ Metaclass that creates a logger instance for all classes derived from  """

    def __new__(mcs, *args, logger_name: typing.Optional[str] = None, **kwargs):
        x = super(LoggedMetaclass, mcs).__new__(mcs, *args, **kwargs)

        # Assign class logger is none exists
        x._cls_logger = elib_logging.get_logger(args[0] + '_cls')
        x._cls_logger.log(elib_logging.META, 'Created')

        return x


class LoggedClass(object, metaclass=LoggedMetaclass):
    """  """

    def __init__(self, logger_instance_name: typing.Optional[str] = None):
        self._obj_logger = elib_logging.get_logger(self.__class__.__name__ + '_' + (logger_instance_name or 'obj'))

    @classes.HybridMethod
    def logger(cls_or_self) -> elib_logging.ExtendedLogger:
        if issubclass(cls_or_self.__class__, LoggedClass):
            return cls_or_self._obj_logger
        else:
            return cls_or_self._cls_logger
