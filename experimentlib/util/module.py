import importlib
import inspect
import pkgutil
import typing


def __recurse_subclasses(subclass_list):
    return_list = []

    for subclass in subclass_list:
        if len(subclass.__subclasses__()) > 0:
            return_list.extend(__recurse_subclasses(subclass.__subclasses__()))

            if not inspect.isabstract(subclass):
                return_list.append(subclass)
        else:
            return_list.append(subclass)

    return return_list


T_OBJECT = typing.TypeVar('T_OBJECT', bound=object)


def get_subclasses(class_root: typing.Type[T_OBJECT]) -> typing.List[typing.Type[T_OBJECT]]:
    """ Get a list of subclasses for a given parent class.

    :param class_root: parent class type
    :return: list
    """
    return __recurse_subclasses([class_root])


def import_submodules(package, recursive=True):
    """ Import all submodules within a given package.

    :param package: base package to begin import from
    :param recursive: if True then import submodules
    """
    if isinstance(package, str):
        package = importlib.import_module(package)

    results = {}

    for loader, name, is_pkg in pkgutil.walk_packages(package.__path__):
        full_name = package.__name__ + '.' + name

        results[full_name] = importlib.import_module(full_name)
        if recursive and is_pkg:
            results.update(import_submodules(full_name))

    return results
