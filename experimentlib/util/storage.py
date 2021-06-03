import abc
import typing


class RegistryEntry(metaclass=abc.ABCMeta):
    """ Interface for classes capable of storage within a Registry. """

    @property
    @abc.abstractmethod
    def registry_name(self) -> str:
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
        super(Registry, self).__init__()

        self._registry: typing.Dict[str, T] = {}

        for item in initial:
            self.register(item)

    def __contains__(self, item):
        return self.registry_str(item) in self._registry

    def __getitem__(self, item):
        return self._registry[self.registry_str(item)]

    def __getattr__(self, item):
        return self[item]

    def register(self, item: T) -> None:
        """ Register an instance with the Registry.

        :param item:
        """
        self._registry[self.registry_str(item.registry_name)] = item

    @classmethod
    def registry_str(cls, x: typing.Any) -> str:
        """ Generate a compatible key from an arbitrary input.

        :param x: input
        :return: Registry compatible key
        """
        if not isinstance(x, str):
            x = str(x)

        return x.replace(' ', '_').replace('-', '_').lower()
