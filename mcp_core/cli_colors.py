# core/cli_colors.py

class CliColors:
    """Enhanced color palette matching the server's ModernVisualEngine.COLORS"""

    # Basic colors (for backward compatibility)
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'

    # Core enhanced colors
    MATRIX_GREEN = '\033[38;5;46m'
    NEON_BLUE = '\033[38;5;51m'
    ELECTRIC_PURPLE = '\033[38;5;129m'
    CYBER_ORANGE = '\033[38;5;208m'
    HACKER_RED = '\033[38;5;196m'
    TERMINAL_GRAY = '\033[38;5;240m'
    BRIGHT_WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

    # Enhanced reddish tones and highlighting colors
    BLOOD_RED = '\033[38;5;124m'
    CRIMSON = '\033[38;5;160m'
    DARK_RED = '\033[38;5;88m'
    FIRE_RED = '\033[38;5;202m'
    ROSE_RED = '\033[38;5;167m'
    BURGUNDY = '\033[38;5;52m'
    SCARLET = '\033[38;5;197m'
    RUBY = '\033[38;5;161m'

    # Highlighting colors
    HIGHLIGHT_RED = '\033[48;5;196m\033[38;5;15m'  # Red background, white text
    HIGHLIGHT_YELLOW = '\033[48;5;226m\033[38;5;16m'  # Yellow background, black text
    HIGHLIGHT_GREEN = '\033[48;5;46m\033[38;5;16m'  # Green background, black text
    HIGHLIGHT_BLUE = '\033[48;5;51m\033[38;5;16m'  # Blue background, black text
    HIGHLIGHT_PURPLE = '\033[48;5;129m\033[38;5;15m'  # Purple background, white text

    # Status colors with reddish tones
    SUCCESS = '\033[38;5;46m'  # Bright green
    WARNING = '\033[38;5;208m'  # Orange
    ERROR = '\033[38;5;196m'  # Bright red
    CRITICAL = '\033[48;5;196m\033[38;5;15m\033[1m'  # Red background, white bold text
    INFO = '\033[38;5;51m'  # Cyan
    DEBUG = '\033[38;5;240m'  # Gray

    # Vulnerability severity colors
    VULN_CRITICAL = '\033[48;5;124m\033[38;5;15m\033[1m'  # Dark red background
    VULN_HIGH = '\033[38;5;196m\033[1m'  # Bright red bold
    VULN_MEDIUM = '\033[38;5;208m\033[1m'  # Orange bold
    VULN_LOW = '\033[38;5;226m'  # Yellow
    VULN_INFO = '\033[38;5;51m'  # Cyan

    # Tool status colors
    TOOL_RUNNING = '\033[38;5;46m\033[5m'  # Blinking green
    TOOL_SUCCESS = '\033[38;5;46m\033[1m'  # Bold green
    TOOL_FAILED = '\033[38;5;196m\033[1m'  # Bold red
    TOOL_TIMEOUT = '\033[38;5;208m\033[1m'  # Bold orange
    TOOL_RECOVERY = '\033[38;5;129m\033[1m'  # Bold purple
