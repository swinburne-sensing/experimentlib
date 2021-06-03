import abc
import typing

from experimentlib import logging
from experimentlib.util import classes


class LoggedMetaclass(abc.ABCMeta):
    """ Metaclass that creates a logger instance for all classes derived from  """

    def __new__(mcs, *args, logger_name: typing.Optional[str] = None, **kwargs):
        x = super(LoggedMetaclass, mcs).__new__(mcs, *args, **kwargs)

        # Assign class logger is none exists
        x._cls_logger = logging.get_logger(args[0] + '_cls')
        x._cls_logger.log(logging.META, 'Created')

        return x


class LoggedClass(object, metaclass=LoggedMetaclass):
    def __init__(self, logger_instance_name: typing.Optional[str] = None):
        """ Base class that contains a logger attached to both the class definition (allowing use in class or static
        methods) and to class instances. An optional string can be appended to the logger name.

        :param logger_instance_name: optional string to append to logger name
        """
        self._obj_logger = logging.get_logger(self.__class__.__name__ + '_' + (logger_instance_name or 'obj'))

    @classes.HybridMethod
    def logger(self) -> logging.ExtendedLogger:
        """ Get reference to the logger attached to either this object (if called as an instance method) or class (if
        called as a class method).

        :return: class or instance ExtendedLogger
        """
        if issubclass(self.__class__, LoggedClass):
            return self._obj_logger
        else:
            return self._cls_logger
