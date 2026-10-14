"""Highscore management module for Pac-Man.

Handles persistent highscores in JSON format according to
subject specifications (Chapter V.5 & VI.8).
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any


class HighscoreManager:
    """Manages reading, updating, and saving highscore records."""

    def __init__(self, filename: str = "scores.json") -> None:
        """Initialize the manager with a target filename.

        Args:
            filename: Path to the highscores storage file.
        """
        self.filepath = Path(filename)
        self.scores: List[Dict[str, Any]] = []
        self.load()

    def _sanitize_name(self, name: str) -> str:
        """Sanitize player name: max 10 chars, alphanumeric and spaces only.

        Args:
            name: Raw player name string.

        Returns:
            Sanitized uppercase name (1 to 10 chars, defaults to 'PLAYER').
        """
        cleaned = re.sub(r'[^a-zA-Z0-9 ]', '', name).strip()
        if not cleaned:
            cleaned = "PLAYER"
        return cleaned[:10].upper()

    def load(self) -> None:
        """Load highscores from file safely, falling back on errors."""
        self.scores = []
        if not self.filepath.exists():
            return

        try:
            content = self.filepath.read_text(encoding="utf-8").strip()
            if not content:
                return

            data = json.loads(content)
            if isinstance(data, list):
                for entry in data:
                    if (isinstance(entry, dict) and "name" in entry
                            and "score" in entry):
                        try:
                            score = int(entry["score"])
                            if score < 0:
                                score = 0
                            clean_name = self._sanitize_name(
                                str(entry["name"])
                            )
                            self.scores.append(
                                {"name": clean_name, "score": score}
                            )
                        except (ValueError, TypeError):
                            continue
            self._sort_and_trim()
        except Exception:
            # Chapter V.5: Robust to file errors (missing, invalid, etc.)
            self.scores = []

    def _sort_and_trim(self) -> None:
        """Sort records descending by score and keep at most top 10."""
        self.scores.sort(key=lambda item: int(item["score"]), reverse=True)
        self.scores = self.scores[:10]

    def add_score(self, name: str, score: int) -> None:
        """Add a new score record and keep top 10.

        Args:
            name: Player name.
            score: Player score (non-negative integer).
        """
        clean_name = self._sanitize_name(name)
        clean_score = max(0, int(score))
        self.scores.append({"name": clean_name, "score": clean_score})
        self._sort_and_trim()
        self.save()

    def save(self) -> None:
        """Persist highscores to file safely."""
        try:
            self._sort_and_trim()
            payload = json.dumps(self.scores, indent=2)
            self.filepath.write_text(payload, encoding="utf-8")
        except Exception as err:
            print(f"Warning: Failed to save highscores: {err}")

    def get_top_scores(self) -> List[Dict[str, Any]]:
        """Return the current top 10 scores list."""
        return list(self.scores)
