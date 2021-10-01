import functools
import typing
import sys


class InstanceError(Exception):
    pass


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


def reference_from_str(name: str, parent: typing.Any):
    """ Get a class from a given module given the classes name as a string.

    :param name: Name of the class to instantiate
    :param parent: Parent module of class
    :return: concrete reference
    """
    if type(parent) is str:
        try:
            parent = sys.modules[parent]
        except KeyError:
            raise KeyError(f"Module {parent} is not available")

    return functools.reduce(getattr, name.split('.'), parent)


def instance_from_dict(config: typing.Dict[str, typing.Any], parent: typing.Any):
    """ Instantiate a class from a given module given a dict containing the class name as a value in the dict.

    :param config: Object description as a dict, requires at least a value for 'class'
    :param parent: Parent module of class
    :return: class instance
    """
    if 'class' in config:
        class_name = config.pop('class')

        class_type = reference_from_str(class_name, parent)
        return class_type(**config)
    elif 'method' in config:
        method_name = config.pop('method')

        return reference_from_str(method_name, parent)
    else:
        raise InstanceError('Configuration dictionary requires either "class" or "method" key')


def resolve_global(name: str):
    # Split name
    name = name.split('.')

    # Find root object
    obj_name = name.pop(0)
    obj = __import__(obj_name)

    while len(name) > 0:
        attr_name = name.pop(0)
        obj_name = obj_name + '.' + attr_name

        try:
            obj = getattr(obj, attr_name)
        except AttributeError:
            # Attempt to import module if not already imported
            __import__(obj_name)
            obj = getattr(obj, attr_name)

    return obj
