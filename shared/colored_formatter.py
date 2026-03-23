import logging

# ANSI color codes (inlined to avoid importing from mcp_core)
_COLORS = {
    'DEBUG':    '\033[38;5;240m',  # gray
    'INFO':     '\033[38;5;46m',   # bright green
    'WARNING':  '\033[38;5;208m',  # orange
    'ERROR':    '\033[38;5;196m',  # bright red
    'CRITICAL': '\033[48;5;196m\033[38;5;15m\033[1m',  # red bg, white bold
}
_BRIGHT_WHITE = '\033[97m'
_RESET = '\033[0m'

class ColoredFormatter(logging.Formatter):
    """Enhanced formatter with colors and emojis - matches server styling"""
    COLORS = _COLORS

    EMOJIS = {
        'DEBUG': '🔍',
        'INFO': '',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'CRITICAL': '🔥'
    }

    _stream: object = None

    def format(self, record):
        record = logging.makeLogRecord(record.__dict__)
        emoji = self.EMOJIS.get(record.levelname, '📝')
        color = self.COLORS.get(record.levelname, _BRIGHT_WHITE)

        # Only apply ANSI codes if the handler stream is a real TTY
        stream = getattr(self, '_stream', None)
        use_color = stream.isatty() if stream and hasattr(stream, 'isatty') else False

        if emoji is not None and emoji != '':
            record.msg = f"{color}{emoji} {record.msg}{_RESET}" if use_color else f"{emoji} {record.msg}"
        else:
            record.msg = f"{color}{record.msg}{_RESET}" if use_color else record.msg
        return super().format(record)