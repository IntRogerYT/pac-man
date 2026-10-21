"""Unit tests for the maze generator demonstration script."""

import builtins
import importlib.util
import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any
from unittest.mock import patch

MODULE_PATH = Path(__file__).resolve().parent.parent / "src" / "maze.py"


def load_maze_module(name: str) -> Any:
    """Load src/maze.py as a fresh module."""
    spec = importlib.util.spec_from_file_location(name, MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestMazeScript(unittest.TestCase):
    """Tests for the executable maze script."""

    def test_module_builds_maze(self) -> None:
        """Test importing the script builds a 15x15 maze."""
        with redirect_stdout(io.StringIO()):
            module = load_maze_module("maze_script_test")
        maze = module.matriz_juego
        self.assertEqual(len(maze), 15)
        self.assertTrue(all(len(row) == 15 for row in maze))
        self.assertEqual(module.mi_laberinto.maze, maze)

    def test_module_cells_are_integers(self) -> None:
        """Test every generated maze cell is an integer."""
        with redirect_stdout(io.StringIO()):
            module = load_maze_module("maze_script_cells_test")
        for row in module.matriz_juego:
            for cell in row:
                self.assertIsInstance(cell, int)

    def test_missing_mazegenerator_module(self) -> None:
        """Test a missing mazegenerator module exits with an error."""
        real_import = builtins.__import__

        def fake_import(*args: Any, **kwargs: Any) -> Any:
            """Raise when importing mazegenerator."""
            if args and args[0] == "mazegenerator":
                raise ModuleNotFoundError("missing")
            return real_import(*args, **kwargs)

        with patch("builtins.__import__", side_effect=fake_import):
            with redirect_stderr(io.StringIO()) as stderr:
                with self.assertRaises(SystemExit):
                    load_maze_module("maze_script_missing_test")
        self.assertIn("Missing Module", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
