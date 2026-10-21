"""Unit tests for the highscore management module."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.highscore import HighscoreManager


class TestHighscoreManager(unittest.TestCase):
    """Tests for HighscoreManager behavior."""

    def setUp(self) -> None:
        """Create a temporary directory for score files."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.filepath = Path(self.temp_dir.name) / "scores.json"

    def test_init_missing_file(self) -> None:
        """Test initialization when the score file does not exist."""
        manager = HighscoreManager(str(self.filepath))
        self.assertEqual(manager.scores, [])
        self.assertEqual(manager.get_top_scores(), [])

    def test_sanitize_name(self) -> None:
        """Test name sanitization rules."""
        manager = HighscoreManager(str(self.filepath))
        self.assertEqual(manager._sanitize_name("pl@yer!123"), "PLYER123")
        self.assertEqual(manager._sanitize_name(""), "PLAYER")
        self.assertEqual(manager._sanitize_name("abcdefghijklm"), "ABCDEFGHIJ")

    def test_load_valid_scores(self) -> None:
        """Test loading valid score entries from disk."""
        payload = [
            {"name": "alice", "score": 100},
            {"name": "bob", "score": -5},
            {"name": "carlos", "score": "oops"},
            "invalid_entry",
        ]
        self.filepath.write_text(json.dumps(payload), encoding="utf-8")
        manager = HighscoreManager(str(self.filepath))
        self.assertEqual(len(manager.scores), 2)
        self.assertEqual(manager.scores[0]["name"], "ALICE")
        self.assertEqual(manager.scores[1]["score"], 0)

    def test_load_empty_and_invalid_json(self) -> None:
        """Test loading empty or malformed JSON files."""
        self.filepath.write_text("", encoding="utf-8")
        manager = HighscoreManager(str(self.filepath))
        self.assertEqual(manager.scores, [])

        self.filepath.write_text("{not json", encoding="utf-8")
        manager = HighscoreManager(str(self.filepath))
        self.assertEqual(manager.scores, [])

    def test_load_non_list_json(self) -> None:
        """Test loading JSON that is not a list."""
        self.filepath.write_text(json.dumps({"name": "x"}), encoding="utf-8")
        manager = HighscoreManager(str(self.filepath))
        self.assertEqual(manager.scores, [])

    def test_sort_and_trim(self) -> None:
        """Test sorting and trimming keeps only the top ten."""
        manager = HighscoreManager(str(self.filepath))
        manager.scores = [{"name": f"P{i}", "score": i} for i in range(15)]
        manager._sort_and_trim()
        self.assertEqual(len(manager.scores), 10)
        self.assertEqual(manager.scores[0]["score"], 14)
        self.assertEqual(manager.scores[-1]["score"], 5)

    def test_add_score_and_save(self) -> None:
        """Test adding scores persists them to disk."""
        manager = HighscoreManager(str(self.filepath))
        manager.add_score("alice", 120)
        manager.add_score("bob", 80)
        manager.add_score("carl", 200)
        saved = json.loads(self.filepath.read_text(encoding="utf-8"))
        self.assertEqual(len(saved), 3)
        self.assertEqual(saved[0]["name"], "CARL")
        self.assertEqual(saved[0]["score"], 200)

    def test_add_score_negative(self) -> None:
        """Test negative scores are clamped to zero."""
        manager = HighscoreManager(str(self.filepath))
        manager.add_score("alice", -50)
        self.assertEqual(manager.get_top_scores()[0]["score"], 0)

    def test_save_failure_prints_warning(self) -> None:
        """Test save failure is handled gracefully."""
        manager = HighscoreManager(str(self.filepath))
        with patch.object(Path, "write_text", side_effect=OSError("boom")):
            with patch("builtins.print") as mocked_print:
                manager.save()
                mocked_print.assert_called_once()

    def test_get_top_scores_returns_copy(self) -> None:
        """Test get_top_scores returns a copy of the list."""
        manager = HighscoreManager(str(self.filepath))
        manager.scores = [{"name": "A", "score": 1}]
        result = manager.get_top_scores()
        result.append({"name": "B", "score": 2})
        self.assertEqual(len(manager.scores), 1)


if __name__ == "__main__":
    unittest.main()
