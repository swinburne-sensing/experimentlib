import enum


class Direction(enum.Enum):
    SOURCE = 'source'
    SINK = 'sink'


class Group(enum.Enum):
    """ Definition for known types of hardware or measurements. """

    # Raw data
    RAW = 'raw'

    # Metadata
    LOG = 'log'
    EVENT = 'event'
    STATUS = 'status'

    # Gas flow
    MFC = 'mfc'

    # Gas concentration
    GAS = 'gas'

    # Gas combustion
    COMBUSTION = 'combust'

    # Valve state
    VALVE = 'valve'

    # Internal
    DEBUG = 'debug'

    # Motion
    JERK = 'jerk'
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
    PRESSURE = 'pressure'

    # CV/CC power supply
    SUPPLY = 'supply'

    # Frequency
    FREQUENCY = 'frequency'
    PERIOD = 'period'

    # Complex signals
    TIME_DOMAIN_SAMPLE = 'timedomain'
    FREQUENCY_DOMAIN_SAMPLE = 'freqdomain'
    TIME_FREQUENCY_SAMPLE = 'tfdomain'

    # Particle counts
    PARTICLE_COUNT = 'pn'
    PARTICLE_MASS = 'pm'
