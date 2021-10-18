import logging
import re
import sys
from typing import IO, Mapping, Optional

import colorama

from experimentlib.logging import levels


class ColoramaStreamHandler(logging.StreamHandler):
    """ Colourised stream handler. """
    DEFAULT_COLOR_MAP: Mapping[int, int] = {
        levels.META: colorama.Fore.LIGHTBLUE_EX,
        levels.LOCK: colorama.Style.BRIGHT + colorama.Fore.LIGHTBLACK_EX,
        levels.TRACE: colorama.Style.BRIGHT + colorama.Fore.LIGHTBLACK_EX,
        logging.DEBUG: colorama.Style.RESET_ALL,
        logging.INFO: colorama.Fore.GREEN,
        logging.WARNING: colorama.Style.BRIGHT + colorama.Fore.YELLOW,
        logging.ERROR: colorama.Style.BRIGHT + colorama.Fore.RED,
        logging.CRITICAL: colorama.Back.RED + colorama.Fore.BLACK
    }

    __RE_TRACEBACK = re.compile(r'^[a-z._]+: ', re.IGNORECASE)

    def __init__(self, stream: Optional[IO] = None,
                 color_map: Optional[Mapping[int, int]] = None):
        stream = stream or sys.stdout

        logging.StreamHandler.__init__(self, colorama.AnsiToWin32(stream).stream)

        self.color_map = color_map or self.DEFAULT_COLOR_MAP

    @property
    def is_tty(self):
        # Check if stream is outputting to interactive session
        isatty = getattr(self.stream, 'isatty', None)

        return isatty and isatty()

    def format(self, record: logging.LogRecord):
        message = logging.StreamHandler.format(self, record)

        if self.is_tty:
            message = '\n'.join((self.colorize(line, record) for line in message.split('\n')))

        return message

    def colorize(self, message: str, record: logging.LogRecord):
        try:
            return f"{self.color_map[record.levelno]}{message}{colorama.Style.RESET_ALL}"
        except KeyError:
            return message
