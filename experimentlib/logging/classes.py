import typing
from abc import ABCMeta, abstractmethod

from experimentlib import logging
from experimentlib.util.classes import HybridMethod


class LoggedMetaclass(ABCMeta):
    """ Metaclass that creates a logger instance for all classes derived from  """

    def __new__(mcs, *args, logger_name: typing.Optional[str] = None, **kwargs):
        x = super(LoggedMetaclass, mcs).__new__(mcs, *args, **kwargs)

        # Assign class logger
        x._logged_cls = logging.get_logger(args[0] + '_cls')
        x._logged_cls.log(logging.META, 'Created')

        return x


class LoggedInterface(metaclass=LoggedMetaclass):
    @abstractmethod
    @HybridMethod
    def logger(self) -> logging.ExtendedLogger:
        pass


class LoggedClass(LoggedInterface, metaclass=LoggedMetaclass):
    def __init__(self, logger_instance_name: typing.Optional[str] = None):
        """ Base class that contains a logger attached to both the class definition (allowing use in class or static
        methods) and to class instances. An optional string can be appended to the logger name.

        :param logger_instance_name: optional string to append to logger name
        """
        self._logged_obj = logging.get_logger(self.__class__.__name__ + '_' + (logger_instance_name or 'obj'))
        self._logged_obj.meta('Created')

    @HybridMethod
    def logger(self) -> logging.ExtendedLogger:
        """ Get reference to the logger attached to either this object (if called as an instance method) or class (if
        called as a class method).

        :return: class or instance ExtendedLogger
        """
        if issubclass(self.__class__, LoggedClass):
            return self._logged_obj
        else:
            return self._logged_cls
