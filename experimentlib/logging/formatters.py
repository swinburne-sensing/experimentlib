import html
import logging
import re


class InfluxDBFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        lines = [record.getMessage().strip()]

        if record.exc_info:
            lines.extend([''] + self.formatException(record.exc_info).split('\n'))

        return '\n'.join(lines)


class PushoverFormatter(logging.Formatter):
    _MSG_CHAR_LIMIT = 1024

    _RE_EXC_FILE = re.compile(r'^\s*File "([^,]+)",[^\d]*([\d]+), in\s+(.*)$')

    def format(self, record: logging.LogRecord) -> str:
        msg_lines = [
            record.getMessage().strip(),
            '',
            f"<b>Logger:</b> {record.name}",
            f"<b>Level:</b> {record.levelname}",
            f"<b>File:</b> {record.filename}:{record.lineno}"
        ]

        if record.threadName:
            msg_lines.append(f"<b>Thread:</b> {record.threadName} (id: {record.thread})")

        if record.processName:
            msg_lines.append(f"<b>Process:</b> {record.processName} (id: {record.process})")

        msg = '\n'.join(msg_lines)

        if record.exc_info:
            msg_lines = []

            # Get allowable length
            msg_remaining = self._MSG_CHAR_LIMIT - len(msg)

            # Get a summarised version of the traceback
            exc_lines = self.formatException(record.exc_info).split('\n')

            traceback_flag = False
            traceback_code = None
            traceback_file = None

            for exc_line in exc_lines:
                if traceback_flag:
                    if exc_line.startswith('    '):
                        traceback_code = exc_line.strip()
                    elif exc_line.startswith('  '):
                        traceback_file_match = self._RE_EXC_FILE.match(exc_line)

                        if traceback_file is not None:
                            traceback_file = f"{html.escape(traceback_file_match[3])} in " \
                                             f"\"{traceback_file_match[1]}\", line {traceback_file_match[2]}"
                    else:
                        # Last line of traceback contains exception type and message
                        msg_lines.extend([
                            '',
                            f"<b>Exception:</b> {exc_line.strip()}",
                            f"  <b>from:</b> {traceback_file}",
                            f"  <b>code:</b> <tt>{traceback_code}</tt>"
                        ])

                        traceback_flag = False
                elif exc_line.startswith('Traceback '):
                    traceback_flag = True
                    traceback_code = 'unknown'
                    traceback_file = 'unknown'
                    continue

            exc_msg = '\n'.join(msg_lines)

            if len(exc_msg) > msg_remaining:
                # Truncate exception lines
                exc_msg = exc_msg[:msg_remaining]

            msg += exc_msg

        return msg
