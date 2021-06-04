import threading
import typing

from experimentlib.logging import classes


class LoggedThreadLock(classes.LoggedClass):
    def __init__(self, name: typing.Optional[str] = None, reenterant: bool = True):
        super(LoggedThreadLock, self).__init__(name)

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
        return self.acquire()

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
