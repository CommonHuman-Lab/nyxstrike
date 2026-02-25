# Global configuration for HexStrike AI Community Edition

_config = {
    "APP_NAME": "HexStrike AI Community Edition",
    "VERSION": "1.0.11",
    "COMMAND_TIMEOUT": 300,
    "CACHE_SIZE": 1000,
    "CACHE_TTL": 3600,  # 1 hour
    "DEFAULT_HEXSTRIKE_SERVER": "http://127.0.0.1:8888",
    "MAX_RETRIES": 3,
    "WORD_LISTS": {

        # --- Password Lists ---
        "rockyou": {
            "path": "/usr/share/wordlists/rockyou.txt",
            "type": "password",
            "description": "Common password list for brute-force attacks",
            "recommended_for": ["password_cracking", "login_fuzzing"],
            "size": 14344392,
            "tool": ["john", "hydra"],
            "speed": "slow",
            "language": "en",
            "coverage": "broad",
            "format": "txt"
        },
        "john": {
            "path": "/usr/share/wordlists/john.lst",
            "type": "password",
            "description": "John the Ripper password list",
            "recommended_for": ["password_cracking", "john"],
            "size": 3559,
            "tool": ["john"],
            "speed": "fast",
            "language": "en",
            "coverage": "focused",
            "format": "lst"
        },

        # --- Directory Lists ---
        "common_dirb": {
            "path": "/usr/share/wordlists/dirb/common.txt",
            "type": "directory",
            "description": "Common directory names for web discovery",
            "recommended_for": ["dirbusting", "web_content_discovery"],
            "size": 4614,
            "tool": ["dirb"],
            "speed": "medium",
            "language": "en",
            "coverage": "broad",
            "format": "txt"
        },
        "big_dirb": {
            "path": "/usr/share/wordlists/dirb/big.txt",
            "type": "directory",
            "description": "Large directory wordlist for web discovery",
            "recommended_for": ["dirbusting"],
            "size": 20469,
            "tool": ["dirb"],
            "speed": "slow",
            "language": "en",
            "coverage": "broad",
            "format": "txt"
        },
        "small_dirb": {
            "path": "/usr/share/wordlists/dirb/small.txt",
            "type": "directory",
            "description": "Small directory wordlist for quick scans",
            "recommended_for": ["dirbusting"],
            "size": 959,
            "tool": ["dirb"],
            "speed": "fast",
            "language": "en",
            "coverage": "focused",
            "format": "txt"
        },
        "common_dirsearch": {
            "path": "/usr/share/wordlists/dirsearch/common.txt",
            "type": "directory",
            "description": "Common directory names for Dirsearch",
            "recommended_for": ["dirsearch", "web_content_discovery"],
            "size": 2205,
            "tool": ["dirsearch"],
            "speed": "medium",
            "language": "en",
            "coverage": "focused",
            "format": "txt"
        }
    }
}