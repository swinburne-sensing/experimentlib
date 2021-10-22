import contextlib
import threading
import time
import typing
from datetime import datetime

from experimentlib.data import unit
from experimentlib.logging import classes


class LoggedThreadLock(classes.Logged, contextlib.AbstractContextManager):
    def __init__(self, name: typing.Optional[str] = None, reenterant: bool = True):
        classes.Logged.__init__(self, name)
        contextlib.AbstractContextManager.__init__(self)

        self._reenterant = reenterant

        if self._reenterant:
            self._lock = threading.RLock()
        else:
            self._lock = threading.Lock()

        self._reenterant_depth = 0
        self._owner: typing.Optional[threading.Thread] = None

    def _get_owner(self) -> typing.Optional[threading.Thread]:
        if self._owner:
            if not self._owner.isAlive():
                self.logger().error('Lock owner no longer alive')
                self._owner = None

        return self._owner

    def acquire(self, blocking: bool = True, timeout: typing.Optional[float] = None) -> bool:
        """ Acquire the lock, optionally blocking and optionally timing out if unavailable.

        :param blocking: if True this call blocks until the lock is available or the timeout expires, False for
        non-blocking
        :param timeout:
        :return:
        """
        if blocking:
            if timeout:
                self.logger().lock(f"Blocking on lock acquisition (timeout: {timeout:.3g} s)")
            else:
                self.logger().lock(f"Blocking on lock acquisition (no timeout)")

        state = self._lock.acquire(blocking, timeout or -1)

        if state:
            self._reenterant_depth += 1
            self._owner = threading.current_thread()

            if self._reenterant:
                self.logger().lock(f"Acquired lock (current depth: {self._reenterant_depth})")
            else:
                self.logger().lock('Acquired lock')
        else:
            if self._reenterant:
                if self._owner:
                    self.logger().lock(f"Failed to acquire lock, acquired by thread {self._owner.name} "
                                       f"(id: {self._owner.ident})")
                else:
                    self.logger().lock('Failed to acquire, acquired by unknown')
            else:
                self.logger().lock('Failed to acquire lock')

        return state

    def __enter__(self):
        self.acquire()

        return self

    def release(self) -> None:
        self._lock.release()

        self._reenterant_depth -= 1

        if self._reenterant:
            self.logger().lock(f"Lock released (current depth: {self._reenterant_depth})")
        else:
            self.logger().lock('Lock released')

        # Clear owner
        if self._reenterant_depth == 0:
            self._owner = None

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


class IntervalLock(classes.Logged):
    def __init__(self, name: typing.Optional[str] = None):
        classes.Logged.__init__(self, name)

        self._interval_timeout: typing.Optional[datetime] = None

        if name is not None:
            name += '_internal'

        self._lock = LoggedThreadLock(name, False)

    @contextlib.contextmanager
    def interval(self, minimum_delay: typing.Optional[unit.T_PARSE_QUANTITY]):
        if minimum_delay is not None:
            minimum_delay = unit.parse_timedelta(minimum_delay)

        self._lock.acquire()

        if self._interval_timeout is not None:
            wait_time = self._interval_timeout - datetime.now()

            if wait_time.total_seconds() > 0:
                self.logger().lock(f"Waiting {wait_time}")
                time.sleep(wait_time.total_seconds())
                self._interval_timeout = None

        try:
            yield
        finally:
            # Save exit time
            if minimum_delay is not None:
                self._interval_timeout = datetime.now() + minimum_delay

            self._lock.release()

    def reset(self):
        with self._lock:
            self._interval_timeout = None
            self.logger().lock('Interval reset')
