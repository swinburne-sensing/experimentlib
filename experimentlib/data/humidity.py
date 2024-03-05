import math
import typing

from experimentlib.data import unit


_TYPE_INPUT = typing.Union[unit.Quantity, float, str]


# Humidity calculation constants
_H20_T_CRITICAL = unit.Quantity(647.0096, unit.registry.degK)
_H20_P_CRITICAL = unit.Quantity(22.064000, unit.registry.MPa)
_PWS_C1 = -7.85951783
_PWS_C2 = 1.84408259
_PWS_C3 = -11.7866497
_PWS_C4 = 22.6807411
_PWS_C5 = -15.9618719
_PWS_C6 = 1.80122502
_HUMID_ABS_C = unit.Quantity(2.16679, unit.registry.g * unit.registry.degK / unit.registry.J)

unit_abs = unit.registry.g / pow(unit.registry.meter, 3)
unit_rel = unit.registry.pct

_RH_FULL = unit.Quantity(100, unit_rel)


class HumidityCalculationError(ValueError):
    pass


def _humidity_calc_pws_exp_constants(temperature: unit.Quantity) -> typing.Tuple[float, float, float]:
    temperature_mag = temperature.m_as('degC')

    if -70 <= temperature_mag <= 0:
        a = 6.114742
        m = 9.778707
        tn = 273.1466
    elif 0 < temperature_mag <= 50:
        a = 6.116441
        m = 7.591386
        tn = 240.7263
    elif 50 < temperature_mag <= 100:
        a = 6.004918
        m = 7.337936
        tn = 229.3975
    elif 100 < temperature_mag <= 150:
        a = 5.856548
        m = 7.27731
        tn = 225.1033
    else:
        raise HumidityCalculationError(f"Temperature {temperature!s} outside supported range")

    return a, m, tn


def _humidity_calc_pws_exp(temperature: unit.Quantity) -> unit.Quantity:
    temperature = temperature
    temperature_mag = temperature.m_as('degC')

    (a, m, tn) = _humidity_calc_pws_exp_constants(temperature)

    return unit.Quantity(a * pow(10, (m * temperature_mag) / (temperature_mag + tn)), unit.registry.hPa)


def abs_to_dew(temperature: _TYPE_INPUT, absolute_humidity: _TYPE_INPUT) -> unit.Quantity:
    """ Convert absolute humidity concentration (g/m^3) to a dew point temperature at a specific gas temperature.

    :param temperature: temperature of gas
    :param absolute_humidity: water concentration in gas
    :return: dew point temperature as Quantity
    """
    return rel_to_dew(temperature, abs_to_rel(temperature, absolute_humidity))


def abs_to_rel(temperature: _TYPE_INPUT, absolute_humidity: _TYPE_INPUT) -> unit.Quantity:
    """ Convert absolute humidity concentration (g/m^3) to a relative humidity (%) at a specific gas temperature.

    :param temperature: temperature of the gas
    :param absolute_humidity: water concentration in gas
    :return: relative humidity percentage as Quantity
    """
    temperature_qty = unit.parse(temperature, unit.registry.degC).to(unit.registry.degK)
    absolute_humidity_qty = unit.parse(absolute_humidity, unit_abs)

    pw = temperature_qty * absolute_humidity_qty / _HUMID_ABS_C

    return unit.Quantity((pw / _humidity_calc_pws_exp(temperature_qty)).magnitude, unit_rel)


# Calculate absolute humidity from dew point
def dew_to_abs(dew_temperature: _TYPE_INPUT) -> unit.Quantity:
    """ Convert dew point temperature to absolute humidity.

    :param dew_temperature: dew point temperature
    :return: water concentration in gas as Quantity
    """
    return rel_to_abs(dew_temperature, _RH_FULL)


# Calculate relative humidity from temperature and dew point
def dew_to_rel(temperature: _TYPE_INPUT, dew_temperature: _TYPE_INPUT) -> unit.Quantity:
    """ Convert dew point temperature to relative humidity.

    :param temperature: temperature of gas
    :param dew_temperature: dew point temperature
    :return:
    """
    temperature = unit.parse(temperature, unit.registry.degC)
    dew_temperature = unit.parse(dew_temperature, unit.registry.degC)

    pws = _humidity_calc_pws_exp(temperature)
    pwd = _humidity_calc_pws_exp(dew_temperature)

    return unit.Quantity(pwd / pws, unit.dimensionless).to(unit_rel)  # type:ignore[no-any-return]


# Calculate dew point from temperature and relative_humidity
def rel_to_dew(temperature: _TYPE_INPUT, relative_humidity: _TYPE_INPUT) -> unit.Quantity:
    """ Convert relative humidity to dew point temperature.

    :param temperature: temperature of gas
    :param relative_humidity:
    :return: dew point temperature as Quantity
    """
    temperature = unit.parse(temperature, unit.registry.degC)
    relative_humidity = unit.parse(relative_humidity, unit.dimensionless)

    (a, m, tn) = _humidity_calc_pws_exp_constants(temperature)
    pws = _humidity_calc_pws_exp(temperature) * relative_humidity.m_as(unit.dimensionless)

    return unit.Quantity(tn / (m / (math.log10(pws.m_as('hPa') / a)) - 1), unit.registry.degC)


# Calculate absolute humidity from temperature and relative humidity measurement
def rel_to_abs(temperature: _TYPE_INPUT, relative_humidity: _TYPE_INPUT) -> unit.Quantity:
    """ Convert a relative humidity (%) at a specific temperature to absolute humidity concentration (g/m^3).

    :param temperature: temperature of gas
    :param relative_humidity:
    :return: water concentration in gas as Quantity
    """
    # Convert types
    temperature = unit.parse(temperature, unit.registry.degC)
    relative_humidity = unit.parse(relative_humidity, unit.dimensionless)

    pw = _humidity_calc_pws_exp(temperature) * relative_humidity.m_as(unit.dimensionless)

    return unit.Quantity((_HUMID_ABS_C * pw.to('Pa') / temperature).magnitude, unit_abs)
