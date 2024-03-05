import abc
import typing


class RegistryEntry(metaclass=abc.ABCMeta):
    """ Interface for classes capable of storage within a Registry. """

    @property
    @abc.abstractmethod
    def registry_key(self) -> str:
        """ Get the unique identifier for this object when placed in a Registry. Must be a valid Python attribute name
        (ie. no special characters except '_', preferably lower case).

        :return: str
        """
        pass


T = typing.TypeVar('T', bound=RegistryEntry)


class Registry(typing.Generic[T]):
    """ Registry of instantiated classes. """

    def __init__(self, initial: typing.Optional[typing.Iterable[T]] = None):
        """

        :param initial: iterable for initial insertion into this Registry
        """
        self._registry: typing.Dict[str, T] = {}

        if initial:
            for item in initial:
                self.register(item)

    def __contains__(self, item: typing.Any) -> bool:
        return self._safe_key(item) in self._registry

    def __getitem__(self, item: typing.Any) -> T:
        return self._registry[self._safe_key(item)]

    def __getattr__(self, item: typing.Any) -> T:
        return self[item]

    def __iter__(self) -> typing.Iterator[T]:
        return iter(self._registry.values())

    def register(self, item: T) -> None:
        """ Register an instance with the Registry.

        :param item:
        """
        self._registry[self._safe_key(item.registry_key)] = item

    @classmethod
    def _safe_key(cls, x: typing.Any) -> str:
        """ Generate a safe key from arbitrary input.

        :param x: input
        :return: Registry compatible key
        """
        return str(x).replace(' ', '_').replace('-', '_').lower()
