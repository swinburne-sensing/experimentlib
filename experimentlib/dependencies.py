from attr import __version__ as __attrs_version
from colorama import __version__ as __colorama_version
from influxdb_client import __version__ as __influxdb_client_version
from pandas import __version__ as __pandas_version
from pint import __version__ as __pint_version
from yaml import __version__ as __yaml_version
from regex import __version__ as __regex_version
# noinspection PyProtectedMember
from urllib3 import __version__ as _urllib3_version


__all__ = ['versions', 'python_tested']

versions = {
    'attrs': __attrs_version,
    'colorama': __colorama_version,
    'influxdb_client': __influxdb_client_version,
    'pandas': __pandas_version,
    'pint': __pint_version,
    'python-pushover': '0.4',
    'pyyaml': __yaml_version,
    'rexeg': __regex_version,
    'tenacity': '7.0.0',
    'tzlocal': '2.1',
    'urllib3': _urllib3_version
}

python_tested = [(3, 9)]
