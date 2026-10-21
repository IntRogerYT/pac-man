"""Unit tests for the configuration parser module."""

import unittest
from typing import Dict, Any
from pydantic import ValidationError
from src.parser import LevelConfig, Pacman_Parser


class TestLevelConfig(unittest.TestCase):
    """Tests for LevelConfig model and validators."""

    def test_default_level_config(self) -> None:
        """Test default LevelConfig instantiation."""
        cfg = LevelConfig(
            level_id=1,
            width=15,
            height=15,
            level_max_time=142,
            pacgum=10,
            seed=123,
        )
        self.assertEqual(cfg.level_id, 1)
        self.assertEqual(cfg.width, 15)

    def test_clamp_level_values_non_dict(self) -> None:
        """Test the level validator with non-dictionary input."""
        cfg = LevelConfig.model_validate("invalid_input")
        self.assertEqual(cfg.level_id, 1)
        self.assertEqual(cfg.width, 15)
        self.assertEqual(cfg.height, 15)

    def test_clamp_level_values_out_of_bounds(self) -> None:
        """Test the level validator clamps out of bound numbers."""
        data: Dict[str, Any] = {
            "level_id": -5,
            "width": 100,
            "height": 2,
            "level_max_time": 10,
            "pacgum": 500,
            "seed": "invalid_seed",
        }
        cfg = LevelConfig.model_validate(data)
        self.assertEqual(cfg.level_id, 1)
        self.assertEqual(cfg.width, 42)
        self.assertEqual(cfg.height, 5)
        self.assertEqual(cfg.level_max_time, 42)
        self.assertIsInstance(cfg.seed, int)

    def test_clamp_level_values_valid_seed(self) -> None:
        """Test the level validator keeps a valid integer seed."""
        data: Dict[str, Any] = {
            "level_id": 2,
            "width": 10,
            "height": 10,
            "level_max_time": 100,
            "pacgum": 5,
            "seed": 42,
        }
        cfg = LevelConfig.model_validate(data)
        self.assertEqual(cfg.seed, 42)


class TestPacmanParser(unittest.TestCase):
    """Tests for Pacman_Parser model and global validators."""

    def test_clamp_global_values_valid(self) -> None:
        """Test the global validator with valid parameters."""
        levels = [{"level_id": i + 1} for i in range(10)]
        data: Dict[str, Any] = {
            "highscore_filename": "scores.txt",
            "lives": 3,
            "points_per_pacgum": 10,
            "points_per_super_pacgum": 50,
            "points_per_ghost": 200,
            "levels": levels,
        }
        config = Pacman_Parser.model_validate(data)
        self.assertEqual(config.lives, 3)
        self.assertEqual(len(config.levels), 10)

    def test_clamp_global_values_invalid_types(self) -> None:
        """Test the global validator with invalid types and levels."""
        data: Dict[str, Any] = {
            "highscore_filename": "bad/filename.txt",
            "lives": -10,
            "points_per_pacgum": "abc",
            "points_per_super_pacgum": 5,
            "points_per_ghost": 10,
            "levels": "not_a_list",
        }
        config = Pacman_Parser.model_validate(data)
        self.assertEqual(config.lives, 1)
        self.assertEqual(config.highscore_filename, "scores.txt")
        self.assertEqual(config.points_per_ghost, 200)
        self.assertEqual(len(config.levels), 10)

    def test_clamp_global_values_non_dict(self) -> None:
        """Test the global validator rejects non-dictionary input."""
        with self.assertRaises(ValidationError):
            Pacman_Parser.model_validate(None)

    def test_clamp_global_values_level_id_reordering(self) -> None:
        """Test sequential level ID reordering."""
        levels = [{"level_id": 99}, "invalid_level_item", {"level_id": 2}]
        data: Dict[str, Any] = {
            "highscore_filename": "scores.txt",
            "lives": 3,
            "points_per_pacgum": 10,
            "points_per_super_pacgum": 50,
            "points_per_ghost": 200,
            "levels": levels,
        }
        config = Pacman_Parser.model_validate(data)
        self.assertEqual(config.levels[0].level_id, 1)
        self.assertEqual(config.levels[1].level_id, 2)
        self.assertEqual(config.levels[2].level_id, 3)


if __name__ == "__main__":
    unittest.main()
