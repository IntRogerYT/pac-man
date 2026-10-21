"""Unit tests for the main pac-man entry point."""

import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any, List, Tuple
from unittest.mock import MagicMock, patch

from pydantic import ValidationError

from src.parser import Pacman_Parser

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

MODULE_PATH = Path(__file__).resolve().parent.parent / "pac-man.py"
SPEC = importlib.util.spec_from_file_location("pac_man", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
PACMAN_MODULE: Any = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PACMAN_MODULE)


def make_config() -> Pacman_Parser:
    """Build a valid parser configuration for tests."""
    levels: List[dict[str, int]] = []
    for i in range(10):
        levels.append(
            {
                "level_id": i + 1,
                "width": 5,
                "height": 5,
                "level_max_time": 100,
                "pacgum": 3,
                "seed": i + 1,
            }
        )
    return Pacman_Parser.model_validate(
        {
            "highscore_filename": "scores.json",
            "lives": 3,
            "points_per_pacgum": 10,
            "points_per_super_pacgum": 50,
            "points_per_ghost": 200,
            "levels": levels,
        }
    )


class FakeMazeGenerator:
    """Maze generator stub used by main tests."""

    def __init__(self, size: Tuple[int, int], seed: int,
                 perfect: bool) -> None:
        """Create an open maze of the requested size."""
        width, height = size
        self.maze = [[0 for _ in range(width)] for _ in range(height)]

    def generate(self) -> None:
        """Generate the maze."""


class BrokenMazeGenerator:
    """Maze generator stub that always fails."""

    def __init__(self, size: Tuple[int, int], seed: int,
                 perfect: bool) -> None:
        """Store arguments before failing."""

    def generate(self) -> None:
        """Raise a generation error."""
        raise RuntimeError("boom")


class InterruptRenderer:
    """Renderer stub that raises KeyboardInterrupt."""

    def __init__(self, config: Pacman_Parser,
                 mazes: List[List[List[int]]]) -> None:
        """Store arguments."""

    def run(self) -> None:
        """Interrupt the game loop."""
        raise KeyboardInterrupt


class TestStripComments(unittest.TestCase):
    """Tests for the strip_comments helper."""

    def test_strip_comments(self) -> None:
        """Test commented lines are removed."""
        content = "# header\n{\n  \"a\": 1\n}\n   # indented\n"
        result = PACMAN_MODULE.strip_comments(content)
        self.assertNotIn("header", result)
        self.assertNotIn("indented", result)
        self.assertIn("\"a\": 1", result)


class TestLoadConfig(unittest.TestCase):
    """Tests for the load_config helper."""

    def setUp(self) -> None:
        """Create a temporary directory."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.directory = Path(self.temp_dir.name)

    def test_load_config_valid(self) -> None:
        """Test loading a valid configuration file."""
        path = self.directory / "config.json"
        path.write_text(
            json.dumps(
                {
                    "highscore_filename": "scores.json",
                    "lives": 5,
                    "levels": [],
                }
            ),
            encoding="utf-8",
        )
        config = PACMAN_MODULE.load_config(str(path))
        self.assertEqual(config.lives, 5)
        self.assertEqual(len(config.levels), 10)

    def test_load_config_with_comments(self) -> None:
        """Test comments are stripped before parsing JSON."""
        path = self.directory / "config.json"
        path.write_text(
            "# comment\n{\n  \"highscore_filename\": \"scores.json\",\n"
            "  \"lives\": 4\n}\n",
            encoding="utf-8",
        )
        config = PACMAN_MODULE.load_config(str(path))
        self.assertEqual(config.lives, 4)

    def test_load_config_defaults(self) -> None:
        """Test missing values fall back to defaults."""
        path = self.directory / "config.json"
        path.write_text(
            json.dumps({"highscore_filename": "scores.json"}),
            encoding="utf-8",
        )
        config = PACMAN_MODULE.load_config(str(path))
        self.assertEqual(config.lives, 3)
        self.assertEqual(len(config.levels), 10)

    def test_load_config_empty_file(self) -> None:
        """Test an empty configuration file is rejected."""
        path = self.directory / "config.json"
        path.write_text("", encoding="utf-8")
        with self.assertRaises(SystemExit) as ctx:
            PACMAN_MODULE.load_config(str(path))
        self.assertIn("Invalid configuration", str(ctx.exception))

    def test_load_config_bad_extension(self) -> None:
        """Test non-json extensions are rejected."""
        with self.assertRaises(SystemExit) as ctx:
            PACMAN_MODULE.load_config("config.txt")
        self.assertIn(".json", str(ctx.exception))

    def test_load_config_missing_file(self) -> None:
        """Test a missing configuration file is rejected."""
        path = self.directory / "missing.json"
        with self.assertRaises(SystemExit) as ctx:
            PACMAN_MODULE.load_config(str(path))
        self.assertIn("not found", str(ctx.exception))

    def test_load_config_corrupted_json(self) -> None:
        """Test corrupted JSON is reported as invalid."""
        path = self.directory / "config.json"
        path.write_text("{broken", encoding="utf-8")
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as ctx:
                PACMAN_MODULE.load_config(str(path))
        self.assertIn("Invalid configuration", str(ctx.exception))

    def test_load_config_permission_error(self) -> None:
        """Test permission errors are reported."""
        path = self.directory / "config.json"
        path.write_text("{}", encoding="utf-8")
        with patch.object(Path, "read_text", side_effect=PermissionError):
            with self.assertRaises(SystemExit) as ctx:
                PACMAN_MODULE.load_config(str(path))
        self.assertIn("Permission denied", str(ctx.exception))

    def test_load_config_unicode_error(self) -> None:
        """Test invalid UTF-8 is reported."""
        path = self.directory / "config.json"
        path.write_text("{}", encoding="utf-8")
        error = UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid")
        with patch.object(Path, "read_text", side_effect=error):
            with self.assertRaises(SystemExit) as ctx:
                PACMAN_MODULE.load_config(str(path))
        self.assertIn("UTF-8", str(ctx.exception))

    def test_load_config_validation_error(self) -> None:
        """Test validation errors are reported."""
        path = self.directory / "config.json"
        path.write_text("{}", encoding="utf-8")
        error = ValidationError.from_exception_data("test", [])
        with patch.object(
            Pacman_Parser, "model_validate", side_effect=error
        ):
            with self.assertRaises(SystemExit) as ctx:
                PACMAN_MODULE.load_config(str(path))
        self.assertIn("Invalid configuration", str(ctx.exception))

    def test_load_config_unexpected_error(self) -> None:
        """Test unexpected errors are reported."""
        path = self.directory / "config.json"
        path.write_text("{}", encoding="utf-8")
        with patch.object(
            Path, "read_text", side_effect=RuntimeError("boom")
        ):
            with self.assertRaises(SystemExit) as ctx:
                PACMAN_MODULE.load_config(str(path))
        self.assertIn("unexpected error", str(ctx.exception))


class TestMain(unittest.TestCase):
    """Tests for the main function."""

    def test_main_requires_one_argument(self) -> None:
        """Test main rejects an invalid argument count."""
        with patch.object(sys, "argv", ["pac-man.py"]):
            with self.assertRaises(SystemExit) as ctx:
                PACMAN_MODULE.main()
        self.assertIn("Invalid number of arguments",
                      str(ctx.exception))

    def test_main_runs_game(self) -> None:
        """Test main loads levels and runs the renderer."""
        config = make_config()
        renderer_cls = MagicMock()
        with patch.object(sys, "argv", ["pac-man.py", "config.json"]):
            with patch.object(
                PACMAN_MODULE, "load_config", return_value=config
            ):
                with patch.object(
                    PACMAN_MODULE, "MazeGenerator", FakeMazeGenerator
                ):
                    with patch.object(
                        PACMAN_MODULE, "Renderer", renderer_cls
                    ):
                        with redirect_stdout(io.StringIO()):
                            PACMAN_MODULE.main()
        renderer_cls.assert_called_once()
        renderer_cls.return_value.run.assert_called_once()

    def test_main_generator_failure(self) -> None:
        """Test maze generation failures are reported."""
        config = make_config()
        with patch.object(sys, "argv", ["pac-man.py", "config.json"]):
            with patch.object(
                PACMAN_MODULE, "load_config", return_value=config
            ):
                with patch.object(
                    PACMAN_MODULE, "MazeGenerator", BrokenMazeGenerator
                ):
                    with redirect_stdout(io.StringIO()):
                        with self.assertRaises(SystemExit) as ctx:
                            PACMAN_MODULE.main()
        self.assertIn("MazeGenerator failed", str(ctx.exception))

    def test_main_keyboard_interrupt(self) -> None:
        """Test keyboard interrupts exit gracefully."""
        config = make_config()
        with patch.object(sys, "argv", ["pac-man.py", "config.json"]):
            with patch.object(
                PACMAN_MODULE, "load_config", return_value=config
            ):
                with patch.object(
                    PACMAN_MODULE, "MazeGenerator", FakeMazeGenerator
                ):
                    with patch.object(
                        PACMAN_MODULE, "Renderer", InterruptRenderer
                    ):
                        with redirect_stdout(io.StringIO()):
                            PACMAN_MODULE.main()


if __name__ == "__main__":
    unittest.main()
