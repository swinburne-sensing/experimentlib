from enum import Enum


__all__ = ['Group']


class Group(Enum):
    """ Definition for known types of measurement. """

    # Metadata
    EVENT = 'event'
    STATUS = 'status'
    SYSLOG = 'syslog'

    # Gas flow
    MFC = 'mfc'

    # Calculated gas concentrations
    GAS = 'gas'

    # Gas combustion measurements
    COMBUSTION = 'combust'

    # Valves
    VALVE = 'valve'

    # Internal
    DEBUG = 'debug'

    # Motion
    ACCELERATION = 'acceleration'
    VELOCITY = 'velocity'
    POSITION = 'position'

    # Electrical measurements
    VOLTAGE = 'voltage'
    CURRENT = 'current'
    RESISTANCE = 'resistance'
    IMPEDANCE = 'impedance'

    # LCR
    CAPACITANCE = 'capacitance'
    INDUCTANCE = 'inductance'
    DISSIPATION = 'dissipation'
    QUALITY = 'quality'

    # Measure current, supply voltage
    CONDUCTOMETRIC_IV = 'conductometric_iv'

    # Measure voltage, supply current
    CONDUCTOMETRIC_VI = 'conductometric_vi'

    # Environmental conditions
    TEMPERATURE = 'temperature'
    HUMIDITY = 'humidity'

    # Power supply
    SUPPLY = 'supply'

    # Frequency
    FREQUENCY = 'frequency'
    PERIOD = 'period'

    # Complex signals
    TIME_DOMAIN_SAMPLE = 'timedomain'
    FREQUENCY_DOMAIN_SAMPLE = 'freqdomain'
    TIME_FREQUENCY_SAMPLE = 'tfdomain'
