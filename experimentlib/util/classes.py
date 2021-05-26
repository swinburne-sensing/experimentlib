import functools
import typing
import sys


class HybridMethod(object):
    """ Hybrid method decorator for methods that can be called on an instance of a class or the class itself.

     From: https://stackoverflow.com/questions/18078744/python-hybrid-between-regular-method-and-classmethod """

    def __init__(self, func):
        self.func = func

    def __get__(self, obj, cls):
        context = obj if obj is not None else cls

        @functools.wraps(self.func)
        def hybrid(*args, **kw):
            return self.func(context, *args, **kw)

        # optional, mimic methods some more
        hybrid.__func__ = hybrid.im_func = self.func
        hybrid.__self__ = hybrid.im_self = context

        return hybrid


def class_from_str(class_name: str, parent: typing.Any):
    """ Get a class from a given module given the classes name as a string.

    :param class_name: Name of the class to instantiate
    :param parent: Parent module of class
    :return: class type
    """
    if type(parent) is str:
        try:
            parent = sys.modules[parent]
        except KeyError:
            raise KeyError(f"Module {parent} is not available")

    return functools.reduce(getattr, class_name.split('.'), parent)


def instance_from_str(class_name: str, parent: typing.Any, *args, **kwargs):
    """ Instantiate a class from a given module given the class name as a string.

    :param class_name: Name of the class to instantiate
    :param parent: Parent module of class
    :param args: Positional arguments to pass to class constructor
    :param kwargs: Keyword arguments to pass to class constructor
    :return: class instance
    """
    class_type = class_from_str(class_name, parent)

    # # Get init arguments and self argument
    # init_parameters = inspect.signature(class_type.__init__).parameters.copy()
    # init_parameters.pop('self')
    #
    # # Validate arguments
    # for arg in args:
    #     init_arg = init_parameters.popitem(last=False)
    #
    # for kwarg_name, kwarg_value in kwargs.items():
    #     init_kwarg = init_parameters.pop(kwarg_name)
    #
    #     if typing_inspect.is_union_type(init_kwarg.annotation):
    #         for init_kwarg_type in typing_inspect.get_args(init_kwarg.annotation):
    #             pass
    #     else:
    #         # Try to cast passed argument
    #         init_kwarg.annotation(kwarg_value)

    return class_type(*args, **kwargs)


def instance_from_dict(class_dict: typing.Dict[str, typing.Any], parent: typing.Any):
    """ Instantiate a class from a given module given a dict containing the class name as a value in the dict.

    :param class_dict: Object description as a dict, requires at least a value for 'class'
    :param parent: Parent module of class
    :return: class instance
    """
    class_name = class_dict.pop('class')

    return instance_from_str(class_name, parent, **class_dict)
