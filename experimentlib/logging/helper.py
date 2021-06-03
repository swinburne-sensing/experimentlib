import getpass
import typing
import platform
import socket
import sys

from experimentlib import logging


def log_system(logger: typing.Optional[logging.ExtendedLogger] = None, level: int = logging.INFO):
    if logger is None:
        logger = logging.get_logger(__name__)

    # Launch arguments
    logger.log(level, f"Launch arguments: {' '.join(sys.argv)}")

    # Platform version
    logger.log(level, "Runtime: python {}".format(sys.version.replace('\n', ' ')))
    logger.log(level, f"Interpreter: {sys.executable}")
    logger.log(level, f"Platform: {platform.python_implementation()}")
    logger.log(level, f"Path: {';'.join(sys.path)}")

    # System information
    logger.log(level, f"Hostname: {socket.getfqdn()}")
    logger.log(level, f"Username: {getpass.getuser()}")
