import typing

import pint


class QuantityParseError(Exception):
    pass


# Handler for percent sign
def _handle_percent(x):
    return x.replace('%', 'pct')


# Unit registry
registry = pint.UnitRegistry(autoconvert_offset_to_baseunit=True, preprocessors=[_handle_percent])

# Shorthand
Quantity = registry.Quantity
Unit = registry.Unit

# Change default printing format
registry.default_format = '.3g~P#'

# Define additional units
registry.define('percent = count / 100 = pct')
registry.define('ppm = count / 1e6')
registry.define('ppb = count / 1e9')

registry.define('standard_cubic_centimeter_per_minute = cm ** 3 / min = sccm')

# Handle pickle/unpickling by overwriting the built-in unit registry
pint.set_application_registry(registry)


# Decorate Quantity formatter to catch printing percent
def _format_decorator(format_method):
    def format_decorator(self, spec):
        spec = spec or self.default_format

        if self.units in (registry.pct, registry.ppm, registry.ppb):
            # Discard custom pint flags
            format_spec = f"{{:{pint.formatting.remove_custom_flags(spec).replace('#', '').replace('g', 'f')}}}"

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
                end_flag = False

                while not end_flag and len(value_str) > 1:
                    end_flag = value_str[-1] == '.'

                    if not end_flag and value_str[-1] != '0':
                        break

                    value_str = value_str[:-1]

            return value_str + scale_str
        else:
            return format_method(self, spec)

    return format_decorator


Quantity.__format__ = _format_decorator(Quantity.__format__)


# Type hints
TYPE_PARSE_VALUE = typing.Union[Quantity, str, float, int]
TYPE_PARSE_UNIT = typing.Union[Unit, str]


def parse(x: TYPE_PARSE_VALUE, to_unit: typing.Optional[TYPE_PARSE_UNIT] = None) -> Quantity:
    """ Parse input to a Quantity of specified unit.

    :param x: input str, number or Quantity
    :param to_unit: str or Unit to convert parsed values to
    :return: Quantity with parsed magnitude and specified unit
    """
    # Parse unit if provided as string
    if isinstance(to_unit, str):
        input_unit = registry[to_unit].units

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
                raise QuantityParseError(f"Unable to convert quantity {x!s} to unit {to_unit}") from ex
        else:
            x = Quantity(x.m_as('dimensionless'), to_unit)

    return x


def converter(to_unit: TYPE_PARSE_UNIT) -> typing.Callable[[TYPE_PARSE_VALUE], Quantity]:
    """ Create wrapper for parse method with a pre-defined unit. Useful with the attrs library.

    :param to_unit:
    :return:
    """
    def f(x: TYPE_PARSE_VALUE):
        return parse(x, to_unit)

    return f


def converter_optional(to_unit: TYPE_PARSE_UNIT) -> typing.Callable[[typing.Optional[TYPE_PARSE_VALUE]], Quantity]:
    """ Create wrapper for parse method with a pre-defined unit. Useful with the attrs library.

    :param to_unit:
    :return:
    """
    def f(x: typing.Optional[TYPE_PARSE_VALUE]):
        if x is None:
            return None

        return parse(x, to_unit)

    return f
