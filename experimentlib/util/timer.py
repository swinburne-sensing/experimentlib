import threading
import typing
from datetime import datetime, timedelta

from experimentlib.logging import classes


class TimeoutLock(classes.Logged):
    def __init__(self, interval: typing.Union[float, timedelta], name: typing.Optional[str] = None):
        classes.Logged.__init__(self, name)

        if isinstance(interval, float):
            self._interval = timedelta(seconds=interval)
        else:
            self._interval = interval

        self._lock = threading.RLock()
        self._trigger: typing.Optional[datetime] = None

    @property
    def interval(self) -> timedelta:
        return self._interval

    @interval.setter
    def interval(self, interval: typing.Union[float, timedelta]):
        if isinstance(interval, float):
            self._interval = timedelta(seconds=interval)
        else:
            self._interval = interval

    def acquire(self):
        pass

    def release(self):
        pass

    def __enter__(self):
        return self.acquire()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

    def reset(self):
        """ Reset timer.
        """
        self._trigger = None
