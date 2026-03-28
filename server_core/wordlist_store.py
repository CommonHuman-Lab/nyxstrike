import json
import logging
import os
from typing import Optional
import server_core.config_core as config_core

logger = logging.getLogger(__name__)

WORDLISTS_FILE_NAME = "wordlists.json"

class WordlistStore:
    """
    Persists user wordlists paths as a single JSON file on disk.
    File layout:
        <data_dir>/wordlists.json      — all wordlist paths in one file
    """

    def __init__(self, data_dir: Optional[str] = None) -> None:
        self._data_dir = data_dir or config_core.default_data_dir()
        self._wordlists_file = os.path.join(self._data_dir, WORDLISTS_FILE_NAME)
        self._ensure_dir_and_file()

    @property
    def data_dir(self) -> str:
        return self._data_dir

    def _ensure_dir_and_file(self) -> None:
        os.makedirs(self._data_dir, exist_ok=True)
        if not os.path.exists(self._wordlists_file):
            with open(self._wordlists_file, "w", encoding="utf-8") as f:
                json.dump({"WORD_LISTS": {}}, f, indent=2)

    def delete(self, wordlist_id: str) -> bool:
        """Delete a wordlist entry by its ID."""
        if not os.path.exists(self._wordlists_file):
            return False
        try:
            with open(self._wordlists_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "WORD_LISTS" in data and wordlist_id in data["WORD_LISTS"]:
                del data["WORD_LISTS"][wordlist_id]
                tmp_path = self._wordlists_file + ".tmp"
                with open(tmp_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, default=str)
                os.replace(tmp_path, self._wordlists_file)
                return True
            return False
        except (OSError, TypeError, json.JSONDecodeError) as exc:
            logger.error(f"💾 Failed to delete wordlist {wordlist_id}: {exc}")
            return False

    def save(self, wordlist_id: str, wordlist_info: dict) -> bool:
        # Ensure required keys are present
        if not isinstance(wordlist_info, dict) or "path" not in wordlist_info or "type" not in wordlist_info:
            logger.error(f"💾 wordlist_info for '{wordlist_id}' must contain at least 'path' and 'type'")
            return False
        try:
            data = {}
            if os.path.exists(self._wordlists_file):
                with open(self._wordlists_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                os.makedirs(os.path.dirname(self._wordlists_file), exist_ok=True)
            if "WORD_LISTS" not in data:
                data["WORD_LISTS"] = {}
            data["WORD_LISTS"][wordlist_id] = wordlist_info
            tmp_path = self._wordlists_file + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
            os.replace(tmp_path, self._wordlists_file)
            return True
        except (OSError, TypeError, json.JSONDecodeError) as exc:
            logger.error(f"💾 Failed to save wordlist {wordlist_id}: {exc}")
            return False
    
    def getPath(self, wordlist_id: str) -> Optional[str]:
        """Get the filesystem path of a wordlist by its ID."""
        wordlist = self.load(wordlist_id)
        if wordlist and "path" in wordlist:
            return wordlist["path"]
        return None

    def load(self, wordlist_id: str) -> Optional[dict]:
        """Load a wordlist entry from the wordlists.json file."""
        if not os.path.exists(self._wordlists_file):
            return None
        try:
            with open(self._wordlists_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("WORD_LISTS", {}).get(wordlist_id)
        except (json.JSONDecodeError, OSError) as exc:
            logger.error(f"💾 Failed to load wordlist {wordlist_id}: {exc}")
            return None

    def load_all(self) -> dict:
        """Load all wordlist entries from wordlists.json."""
        if not os.path.exists(self._wordlists_file):
            return {}
        try:
            with open(self._wordlists_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("WORD_LISTS", {})
        except (json.JSONDecodeError, OSError) as exc:
            logger.error(f"💾 Failed to load all wordlists: {exc}")
            return {}
        
    def find_best_match(self, criteria: dict) -> Optional[dict]:
        """
        Find the best matching wordlist based on given criteria.

        Criteria can include keys like 'for_task', 'tool', 'speed', etc.
        The method will attempt to find the most suitable wordlist based on these criteria.

        Args:
            criteria (dict): A dictionary of criteria to match against wordlist metadata.   
                Supported keys include:
                    - for_task: Task the wordlist is recommended for (matches if value is in 'recommended_for' list)
                    - tool: Tool the wordlist is intended for (matches if value is in 'tool' list)
                    - type: Type of wordlist (e.g., 'password', 'directory')
                    - language: Language of the wordlist (e.g., 'en')
                    - speed: Speed category (e.g., 'fast', 'medium', 'slow')
                    - coverage: Coverage type (e.g., 'broad', 'focused')
                    - format: File format (e.g., 'txt', 'lst')        
        Returns:
            Optional[dict]: The best matching wordlist metadata dictionary, or None if no match is
            found.
        """
        wordlists = self.load_all()
        def matches(wl):
            for key, value in criteria.items():
                if key == "for_task":
                    if value not in wl.get("recommended_for", []):
                        return False
                elif key == "tool":
                    if value not in wl.get("tool", []):
                        return False
                else:
                    if wl.get(key) != value:
                        return False
            return True

        # 1. Exact match for all criteria
        for name, wl in wordlists.items():
            if matches(wl):
                return {"name": name, "wordlist": wl}

        # 2. Relaxed: match at least for_task, then as many as possible
        if "for_task" in criteria:
            for name, wl in wordlists.items():
                if criteria["for_task"] in wl.get("recommended_for", []):
                    return {"name": name, "wordlist": wl}

        # 3. Fallback: return any wordlist
        for name, wl in wordlists.items():
            return {"name": name, "wordlist": wl}
        return None
            