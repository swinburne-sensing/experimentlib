import importlib
import inspect
import pkgutil
from typing import List


def get_call_context(root_module: str, discard_calls: int = 1, filter_app: bool = True) -> List[str]:
    """ Get a list of contextual calls in the stack.

    :param root_module:
    :param discard_calls: number of stacks calls to discard (0 would include call to this method)
    :param filter_app: if True only calls to methods in this application (no external modules or built-ins)
    :return: list
    """
    context = inspect.stack()
    context_list = []

    # Filter stack frames from this application
    if filter_app:
        context = [x for x in context[discard_calls:] if x[1].startswith(root_module)]

    for frame in context:
        frame_path = frame[1]

        if filter_app:
            frame_path = frame_path[len(root_module):]

        context_list.append(f"{frame_path}:{frame[3]}:{frame[2]}")

    return context_list


def import_submodules(package, recursive=True):
    """ Import all submodules within a given package.

    :param package: base package to begin import from
    :param recursive: if True then import submodules
    """
    if isinstance(package, str):
        package = importlib.import_module(package)

    for loader, name, is_pkg in pkgutil.walk_packages(package.__path__):
        full_name = package.__name__ + '.' + name

        importlib.import_module(full_name)

        if recursive and is_pkg:
            import_submodules(full_name)
