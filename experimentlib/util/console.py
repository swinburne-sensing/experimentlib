import logging
import re
import sys

from experimentlib import logging as elib_logging

# Attempt to import colorama
try:
    import colorama


    class ColoramaStreamHandler(logging.StreamHandler):
        """ Colourised stream handler. """
        color_map = {
            elib_logging.META: colorama.Fore.LIGHTBLUE_EX,
            elib_logging.LOCK: colorama.Style.BRIGHT + colorama.Fore.LIGHTBLACK_EX,
            elib_logging.TRACE: colorama.Style.BRIGHT + colorama.Fore.LIGHTBLACK_EX,
            elib_logging.DEBUG: colorama.Style.RESET_ALL,
            elib_logging.INFO: colorama.Fore.GREEN,
            elib_logging.WARNING: colorama.Style.BRIGHT + colorama.Fore.YELLOW,
            elib_logging.ERROR: colorama.Style.BRIGHT + colorama.Fore.RED,
            elib_logging.CRITICAL: colorama.Back.RED + colorama.Fore.BLACK
        }

        __RE_TRACEBACK = re.compile(r'^[a-z._]+: ', re.IGNORECASE)

        def __init__(self, stream, color_map=None):
            super().__init__(colorama.AnsiToWin32(stream).stream)

            if color_map is not None:
                self.color_map = color_map

        @property
        def is_tty(self):
            # Check if stream is outputting to interactive session
            isatty = getattr(self.stream, 'isatty', None)

            return isatty and isatty()

        def format(self, record):
            message = super().format(record)

            if self.is_tty:
                message = '\n'.join((self.colorize(line, record) for line in message.split('\n')))

            return message

        def colorize(self, message: str, record: logging.LogRecord):
            try:
                return self.color_map[record.levelno] + message + colorama.Style.RESET_ALL
            except KeyError:
                return message
except ImportError:
    colorama = None

    # Define dummy handler if colorama is not installed
    class ColoramaStreamHandler(logging.StreamHandler):
        def __init__(self, stream, _):
            logging.StreamHandler.__init__(self, stream)


def basic_logging(level: int = elib_logging.INFO):
    """ Configure basic logging with a coloured stream handler.

    :param level: minimum logging level
    """
    logging.basicConfig(level=level, handlers=[ColoramaStreamHandler(sys.stdout)])
