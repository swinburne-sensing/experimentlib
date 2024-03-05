from abc import ABCMeta
from datetime import timedelta
from time import sleep
from timeit import default_timer
from typing import Any, Dict, Optional, Tuple, Type, TypeVar, Union

from experimentlib import logging
from experimentlib.util.classes import HybridMethod


TMeta = TypeVar('TMeta', bound=type)
TABCMeta = TypeVar('TABCMeta', bound=ABCMeta)


class LoggedMeta(type):
    """ Metaclass that creates a logger instance for all classes derived from  """

    def __new__(cls: Type[TMeta], name: str, bases: Tuple[Type[object]], classdict: Dict[str, str]) -> TMeta:
        x = type.__new__(cls, name, bases, classdict)

        # Assign class logger
        x._logged_cls = logging.get_logger(name + ':cls')  # type: ignore[attr-defined]
        x._logged_cls.log(logging.META, 'Created')  # type: ignore[attr-defined]

        return x


class LoggedAbstractMeta(ABCMeta):
    def __new__(cls: Type[TABCMeta], name: str, bases: Tuple[Type[object]], classdict: Dict[str, str]) -> TABCMeta:
        x = ABCMeta.__new__(cls, name, bases, classdict)

        # Assign class logger
        setattr(x, '_logged_cls', logging.get_logger(name + ':cls'))  # type: ignore[attr-defined]
        x._logged_cls.log(logging.META, 'Created')  # type: ignore[attr-defined]

        return x


class _LoggedBase(object):
    def __init__(self, logger_instance_name: Optional[str] = None):
        """ Base class that contains a logger attached to both the class definition (allowing use in class or static
        methods) and to class instances. An optional string can be appended to the logger name.

        :param logger_instance_name: optional string to append to logger name
        """
        self._logged_obj = logging.get_logger(self.__class__.__name__ + ':' + (logger_instance_name or 'obj'))
        self._logged_obj.meta('Created')

    @HybridMethod
    def logger(self) -> logging.ExtendedLogger:
        """ Get reference to the logger attached to either this object (if called as an instance method) or class (if
        called as a class method).

        :return: class or instance ExtendedLogger
        """
        if issubclass(self.__class__, _LoggedBase):
            return self._logged_obj
        else:
            return self._logged_cls

    def sleep(self, interval: Union[None, int, float, timedelta], cause: Optional[str] = None,
              log_level: Optional[int] = None) -> None:
        """ Sleep for perceribed interval logging the entry and exit time.

        :param interval:
        :param cause:
        :param log_level: log level, defaults to LOCK
        :return:
        """
        log_level = log_level or logging.LOCK

        if isinstance(interval, timedelta):
            interval = interval.total_seconds()

        if interval is None or interval <= 0:
            return

        tic = default_timer()
        self.logger().log(log_level, f"Sleep {interval:.3g} sec (cause: {cause if cause else 'unspecified'})")
        sleep(interval)
        self.logger().log(log_level, f"Sleep complete (cause: {cause if cause else 'unspecified'}, "
                                     f"target: {interval:.3g} sec, actual: {(default_timer() - tic):.6g} sec)")


class Logged(_LoggedBase, metaclass=LoggedMeta):
    pass


class LoggedAbstract(_LoggedBase, metaclass=LoggedAbstractMeta):
    pass
