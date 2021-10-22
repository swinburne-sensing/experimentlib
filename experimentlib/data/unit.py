import functools
import typing
from datetime import timedelta

import pint

import experimentlib

try:
    import pint_pandas
except ImportError:
    pint_pandas = None


class QuantityParseError(experimentlib.ExperimentLibError):
    pass


# Handler for percent sign
def _handle_percent(x):
    return x.replace('%', 'pct')


# Unit registry
registry = pint.UnitRegistry(autoconvert_offset_to_baseunit=True, preprocessors=[_handle_percent])


# Hack to make Quantity objects pickle-able by fixing implementation used in registry
# noinspection PyProtectedMember
class Quantity(pint.quantity._Quantity):
    _REGISTRY = registry


registry.Quantity = Quantity

# Shorthand
# Quantity = registry.Quantity
Unit = registry.Unit

# Change default printing format
registry.default_format = '.3g~P#'

# Define additional units
registry.define('percent = count / 100 = pct')
registry.define('ppm = count / 1e6')
registry.define('ppb = count / 1e9')

registry.define('standard_cubic_centimeter_per_minute = cm ** 3 / min = sccm')
registry.define('cubic_centimeter_per_minute = cm ** 3 / min = ccm')
# registry.define('litre_per_minute = l / min = lpm')

# Add aliases
registry.define('@alias psi = PSI')
registry.define('@alias ccm = CCM')
registry.define('@alias sccm = SCCM')
# registry.define('@alias m ** 3 = m3/d')

# Shortcuts for dimensionless quantities
dimensionless = registry.dimensionless

# Handle pickle/unpickling by overwriting the built-in unit registry
pint.set_application_registry(registry)

# Setup pint arrays
if pint_pandas is not None:
    # noinspection PyUnresolvedReferences
    PintArray = pint_pandas.PintArray
    # noinspection PyUnresolvedReferences
    pint_pandas.PintType.ureg = registry


# Decorate Quantity formatter to catch printing dimensionless units
def _quantity_format_decorator(format_method):
    def format_decorator(self: Quantity, spec):
        spec = spec or self.default_format

        if self.units in (registry.pct, registry.ppm, registry.ppb):
            # Discard custom pint flags
            format_spec = f"{{:{pint.formatting.remove_custom_flags(spec).replace('g', 'f').replace('#', '')}}}"

            abs_mag = self.m_as(registry.dimensionless)

            if abs_mag > 0.001:
                mag = abs_mag * 100
                scale_str = '%'
            elif abs_mag > 1e-7:
                mag = abs_mag * 1e6
                scale_str = ' ppm'
            elif abs_mag > 1e-10:
                mag = abs_mag * 1e9
                scale_str = ' ppb'
            else:
                return str(abs_mag)

            value_str = format_spec.format(mag)

            # Suppress trailing zeros
            if '.' in value_str:
                value_str = value_str.rstrip('0').rstrip('.')

            return value_str + scale_str
        elif self.units.is_compatible_with(registry.sec) and self.magnitude > 1:
            # Discard custom pint flags
            format_spec = f"{{:{pint.formatting.remove_custom_flags(spec).replace('g', 'f').replace('#', '')}}}"

            # Force output directly to seconds
            value_str = format_spec.format(self.m_as(registry.sec))

            # Suppress trailing zeros
            if '.' in value_str:
                value_str = value_str.rstrip('0').rstrip('.')

            return value_str + ' ' + str(registry.sec)
        else:
            value_str = format_method(self, spec)
            value_split = value_str.split(' ', 1)

            # Suppress trailing zeros
            if '.' in value_split[0]:
                value_split[0] = value_split[0].rstrip('0').rstrip('.')

            return ' '.join(value_split)

    return format_decorator


def _unit_format_decorator(format_method):
    def format_decorator(self, spec):
        unit_str = format_method(self, spec)

        if unit_str.endswith('pct'):
            return '%'

        return unit_str

    return format_decorator


Quantity.__format__ = _quantity_format_decorator(Quantity.__format__)
Unit.__format__ = _unit_format_decorator(Unit.__format__)


# Type hints
T_PARSE_QUANTITY = typing.Union[Quantity, str, float, int]
T_PARSE_UNIT = typing.Union[Unit, Quantity, str]
T_PARSE_TIMEDELTA = typing.Union[timedelta, Quantity, str]


def parse_unit(x: T_PARSE_UNIT) -> Unit:
    """ Parse arbitrary input to a Unit from the registry.

    :param x: input str
    :return: Unit
    """
    if isinstance(x, Unit):
        # Already a Unit
        return x

    if isinstance(x, Quantity):
        # Extract Unit, can sometimes occur when using values from pint
        return x.units

    if not isinstance(x, str):
        raise QuantityParseError(f"Unsupported input type \"{type(x)}\"")

    if hasattr(registry, x):
        return getattr(registry, x)

    raise QuantityParseError(f"Unknown unit \"{x}\"")


def parse(x: T_PARSE_QUANTITY, to_unit: typing.Optional[T_PARSE_UNIT] = None, mag_round: typing.Optional[int] = None) \
        -> Quantity:
    """ Parse arbitrary input to a Quantity of specified unit.

    :param x: input str, number or Quantity
    :param to_unit: str or Unit to convert parsed values to
    :param mag_round:
    :return: Quantity with parsed magnitude and specified unit
    """
    if x is None:
        raise QuantityParseError('Cannot convert NoneType to Quantity')

    # Parse unit
    if to_unit is not None:
        to_unit = parse_unit(to_unit)

    if not isinstance(x, Quantity):
        # Convert int to float
        if isinstance(x, int):
            x = float(x)

        # Convert floats (and ints) to Quantity, attempt to directly parse strings
        if isinstance(x, float) or isinstance(x, str):
            x = Quantity(x)
        else:
            raise QuantityParseError(f"Unsupported input type \"{type(x)}\"")

    # Attempt conversion
    if to_unit is not None:
        if not x.unitless:
            try:
                x.ito(to_unit)
            except pint.errors.DimensionalityError as ex:
                raise QuantityParseError(f"Unable to convert parsed quantity {x!s} to unit {to_unit}") from ex
        else:
            x = Quantity(x.m_as(dimensionless), to_unit)

    if mag_round is not None:
        # Round resulting value
        x = round(x, mag_round)

    return x


def parse_magnitude(x: T_PARSE_QUANTITY, magnitude_unit: T_PARSE_UNIT,
                    input_unit: typing.Optional[T_PARSE_UNIT] = None) -> float:
    """ Shortcut method to parse as value, optionally converting to specified unit before returning the magnitude.

    :param x: input str, number or Quantity
    :param magnitude_unit: str or Unit to convert parsed values to before conversion to magnitude
    :param input_unit: str or Unit to convert parsed values to
    :return:
    """
    magnitude_unit = parse_unit(magnitude_unit)

    if input_unit is None:
        # Assume default parsing unit is same as casting unit
        input_unit = magnitude_unit

    return parse(x, input_unit).m_as(magnitude_unit)


def parse_timedelta(x: T_PARSE_TIMEDELTA) -> timedelta:
    """

    :param x:
    :return:
    """
    if isinstance(x, timedelta):
        # Already a timedelta
        return x

    x_unit = parse(x)

    if x_unit.dimensionless:
        # Assume seconds by default
        x_unit = Quantity(x_unit.m_as(dimensionless), registry.sec)

    x_secs = x_unit.m_as(registry.sec)

    return timedelta(seconds=x_secs)


def converter(to_unit: typing.Optional[T_PARSE_UNIT] = None,
              optional: bool = False) -> typing.Callable[[T_PARSE_QUANTITY], Quantity]:
    """ Create wrapper for parse decorator with a pre-defined unit. Useful with the attrs library.

    :param to_unit: str or Unit to convert values to, defaults to unitless
    :param optional: if False
    :return:
    """
    to_unit = to_unit or registry.dimensionless

    def f(x: T_PARSE_QUANTITY):
        if x is None:
            if not optional:
                raise QuantityParseError('Input to converter cannot be None')

            return None

        return parse(x, to_unit)

    return f


def return_converter(to_unit: T_PARSE_UNIT, allow_none: bool = False):
    """ Decorator to convert returned result to a Quantity.

    :param to_unit:
    :param allow_none:
    :return:
    """
    to_unit = parse_unit(to_unit)

    def wrapper_decorator(func):
        @functools.wraps(func)
        def wrapper_result(*args, **kwargs):
            result = func(*args, **kwargs)

            if result is None:
                if not allow_none:
                    raise ValueError('Expected numeric result')

                return None

            if not isinstance(result, Quantity):
                raise ValueError(f"Decorated method returned {type(result)}, expected Quantity")

            return result.to(to_unit)

        return wrapper_result

    return wrapper_decorator
