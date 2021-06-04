from attr import __version__ as __attrs_version
from colorama import __version__ as __colorama_version
# noinspection PyProtectedMember
from influxdb import __version__ as __influxdb_version
from pint import __version__ as __pint_version
from yaml import __version__ as __yaml_version
# noinspection PyProtectedMember
from ratelimit import __version__ as __ratelimit_version

versions = {
    'attrs': __attrs_version,
    'colorama': __colorama_version,
    'pint': __pint_version,
    'python-influxdb': __influxdb_version,
    'python-pushover': '0.4',
    'pyyaml': __yaml_version,
    'ratelimit': __ratelimit_version,
    'tenacity': '7.0.0'
}

python_tested = [(3, 9)]
