"""Unit tests for the game domain model and engine."""

import unittest
from typing import List
from unittest.mock import patch

from src.game import Direction, GameEngine, Ghost
from src.parser import Pacman_Parser


def make_config(lives: int = 3, pacgum: int = 3) -> Pacman_Parser:
    """Build a valid parser configuration for tests."""
    levels: List[dict[str, int]] = []
    for i in range(10):
        levels.append(
            {
                "level_id": i + 1,
                "width": 5,
                "height": 5,
                "level_max_time": 100,
                "pacgum": pacgum,
                "seed": 42 + i,
            }
        )
    return Pacman_Parser.model_validate(
        {
            "highscore_filename": "scores.json",
            "lives": lives,
            "points_per_pacgum": 10,
            "points_per_super_pacgum": 50,
            "points_per_ghost": 200,
            "levels": levels,
        }
    )


def open_maze(size: int = 5) -> List[List[int]]:
    """Build a fully open square maze."""
    return [[0 for _ in range(size)] for _ in range(size)]


def make_engine(
    lives: int = 3, pacgum: int = 3, size: int = 5
) -> GameEngine:
    """Build a game engine with open mazes."""
    mazes = [open_maze(size) for _ in range(10)]
    return GameEngine(make_config(lives, pacgum), mazes)


class TestDirection(unittest.TestCase):
    """Tests for direction constants."""

    def test_direction_values(self) -> None:
        """Test direction tuples and opposites."""
        self.assertEqual(Direction.NONE, (0, 0))
        self.assertEqual(Direction.UP, (0, -1))
        self.assertEqual(Direction.OPPOSITES[Direction.UP], Direction.DOWN)
        self.assertEqual(Direction.OPPOSITES[Direction.RIGHT],
                         Direction.LEFT)
        self.assertEqual(Direction.OPPOSITES[Direction.NONE], Direction.NONE)


class TestGhost(unittest.TestCase):
    """Tests for the Ghost entity."""

    def test_init_and_reset(self) -> None:
        """Test ghost initialization and reset behavior."""
        ghost = Ghost(1, 3, 4, (255, 0, 0), (0, 0), "Blinky")
        self.assertEqual(ghost.start_pos, (3, 4))
        self.assertEqual(ghost.name, "Blinky")
        ghost.x = 9.0
        ghost.y = 9.0
        ghost.dir = Direction.UP
        ghost.is_eaten = True
        ghost.respawn_timer = 3.0
        ghost.reset_to_start()
        self.assertEqual((ghost.x, ghost.y), (3.0, 4.0))
        self.assertEqual(ghost.dir, Direction.NONE)
        self.assertFalse(ghost.is_eaten)
        self.assertEqual(ghost.respawn_timer, 0.0)


class TestGameEngine(unittest.TestCase):
    """Tests for GameEngine state and mechanics."""

    def test_init_and_current_level_config(self) -> None:
        """Test engine initialization and current level config."""
        engine = make_engine()
        self.assertEqual(engine.current_level_idx, 0)
        self.assertEqual(engine.lives, 3)
        self.assertEqual(engine.current_level_config.level_id, 1)
        self.assertEqual(len(engine.ghosts), 4)
        self.assertEqual(len(engine.super_pacgums), 4)

    def test_load_level_out_of_range(self) -> None:
        """Test loading a level beyond available mazes triggers victory."""
        engine = make_engine()
        engine.load_level(99)
        self.assertTrue(engine.is_victory)

    def test_load_level_values(self) -> None:
        """Test level loading sets dimensions, entities and food."""
        engine = make_engine(pacgum=3)
        self.assertEqual(engine.grid_width, 5)
        self.assertEqual(engine.grid_height, 5)
        self.assertEqual(engine.player_spawn, (2, 2))
        self.assertEqual(engine.level_time_remaining, 100.0)
        self.assertEqual(len(engine.pacgums), 3)
        for pos in engine.pacgums:
            self.assertNotEqual(engine.maze[pos[1]][pos[0]], 15)

    def test_load_level_center_wall_relocates_player(self) -> None:
        """Test player relocates when the center cell is closed."""
        mazes = [open_maze() for _ in range(10)]
        mazes[0][2][2] = 15
        engine = GameEngine(make_config(), mazes)
        self.assertNotEqual(engine.player_spawn, (2, 2))
        self.assertNotEqual(mazes[0][engine.player_spawn[1]]
                            [engine.player_spawn[0]], 15)

    def test_load_level_pacgum_defaults_to_all_cells(self) -> None:
        """Test non-positive pacgum count fills all corridor cells."""
        engine = make_engine(pacgum=0)
        expected = 25 - 4 - 1
        self.assertEqual(len(engine.pacgums), expected)

    def test_can_move_out_of_bounds(self) -> None:
        """Test movement outside the grid is blocked."""
        engine = make_engine()
        self.assertFalse(engine.can_move(-1, 0, Direction.RIGHT))
        self.assertFalse(engine.can_move(0, 0, Direction.UP))
        self.assertFalse(engine.can_move(4, 4, Direction.DOWN))

    def test_can_move_closed_cell(self) -> None:
        """Test closed cells cannot be traversed."""
        engine = make_engine()
        engine.maze[2][2] = 15
        self.assertFalse(engine.can_move(2, 2, Direction.UP))
        self.assertFalse(engine.can_move(1, 2, Direction.RIGHT))

    def test_can_move_wall_bits(self) -> None:
        """Test wall bitmask direction checks."""
        engine = make_engine()
        engine.maze[2][2] = 15
        engine.maze[2][2] = 1
        self.assertFalse(engine.can_move(2, 2, Direction.UP))
        self.assertTrue(engine.can_move(2, 2, Direction.RIGHT))
        engine.maze[2][2] = 2
        self.assertFalse(engine.can_move(2, 2, Direction.RIGHT))
        engine.maze[2][2] = 4
        self.assertFalse(engine.can_move(2, 2, Direction.DOWN))
        engine.maze[2][2] = 8
        self.assertFalse(engine.can_move(2, 2, Direction.LEFT))

    def test_can_move_invalid_direction(self) -> None:
        """Test invalid direction vectors are rejected."""
        engine = make_engine()
        self.assertFalse(engine.can_move(2, 2, (2, 2)))

    def test_request_player_direction(self) -> None:
        """Test direction requests are stored."""
        engine = make_engine()
        engine.request_player_direction(Direction.LEFT)
        self.assertEqual(engine.player_next_dir, Direction.LEFT)

    def test_update_early_return(self) -> None:
        """Test update does nothing when the game is finished."""
        engine = make_engine()
        engine.is_game_over = True
        engine.update(1.0)
        self.assertEqual(engine.level_time_remaining, 100.0)

    def test_update_timeout_causes_death(self) -> None:
        """Test a timeout decreases lives and resets the timer."""
        engine = make_engine(lives=3)
        engine.level_time_remaining = 0.5
        engine.update(1.0)
        self.assertEqual(engine.lives, 2)
        self.assertEqual(engine.level_time_remaining, 100.0)

    def test_update_timeout_game_over(self) -> None:
        """Test a timeout with one life ends the game."""
        engine = make_engine(lives=1)
        engine.level_time_remaining = 0.5
        engine.update(1.0)
        self.assertTrue(engine.is_game_over)
        self.assertEqual(engine.game_over_reason, "timeout")

    def test_update_decrements_frightened_timer(self) -> None:
        """Test the frightened timer counts down."""
        engine = make_engine()
        engine.frightened_timer = 1.0
        engine.update(0.5)
        self.assertAlmostEqual(engine.frightened_timer, 0.5)

    def test_update_freezes_ghosts(self) -> None:
        """Test ghost freeze stops ghost movement."""
        engine = make_engine()
        engine.cheat_ghost_freeze = True
        positions = [(g.x, g.y) for g in engine.ghosts]
        engine.update(0.5)
        self.assertEqual([(g.x, g.y) for g in engine.ghosts], positions)

    def test_update_advances_level_when_cleared(self) -> None:
        """Test clearing all food advances to the next level."""
        engine = make_engine()
        engine.pacgums.clear()
        engine.super_pacgums.clear()
        engine.update(0.01)
        self.assertEqual(engine.current_level_idx, 1)

    def test_update_player_reversal(self) -> None:
        """Test immediate reversal of player direction."""
        engine = make_engine()
        engine.player_dir = Direction.RIGHT
        engine.request_player_direction(Direction.LEFT)
        engine._update_player(0.1)
        self.assertEqual(engine.player_dir, Direction.LEFT)

    def test_update_player_corner_snap(self) -> None:
        """Test turning is allowed near the tile center."""
        engine = make_engine()
        engine.player_dir = Direction.UP
        engine.request_player_direction(Direction.RIGHT)
        engine._update_player(0.01)
        self.assertEqual(engine.player_dir, Direction.RIGHT)

    def test_update_player_no_direction(self) -> None:
        """Test player stays still without a direction."""
        engine = make_engine()
        start = (engine.player_x, engine.player_y)
        engine._update_player(1.0)
        self.assertEqual((engine.player_x, engine.player_y), start)

    def test_update_player_speed_boost(self) -> None:
        """Test the speed boost cheat increases movement."""
        engine = make_engine()
        engine.player_dir = Direction.RIGHT
        engine._update_player(0.1)
        normal = engine.player_x
        engine.player_x = 2.0
        engine.cheat_speed_boost = True
        engine._update_player(0.1)
        self.assertGreater(engine.player_x, normal)

    def test_update_player_wall_blocking(self) -> None:
        """Test the player cannot walk through walls."""
        engine = make_engine()
        engine.maze[2][2] = 2
        engine.player_dir = Direction.RIGHT
        engine._update_player(1.0)
        self.assertEqual(engine.player_x, 2.0)

    def test_update_player_vertical_blocking(self) -> None:
        """Test vertical wall blocking clamps position."""
        engine = make_engine()
        engine.maze[2][2] = 4
        engine.player_dir = Direction.DOWN
        engine._update_player(1.0)
        self.assertEqual(engine.player_y, 2.0)
        engine.maze[2][2] = 1
        engine.player_y = 2.0
        engine.player_dir = Direction.UP
        engine._update_player(1.0)
        self.assertEqual(engine.player_y, 2.0)

    def test_get_ghost_targets(self) -> None:
        """Test personality targets for all ghosts."""
        engine = make_engine()
        engine.player_x, engine.player_y = 2.0, 2.0
        engine.player_dir = Direction.RIGHT
        blinky, pinky, inky, clyde = engine.ghosts
        self.assertEqual(engine._get_ghost_target(blinky), (2.0, 2.0))
        self.assertEqual(engine._get_ghost_target(pinky), (6.0, 2.0))
        inky_target = engine._get_ghost_target(inky)
        self.assertIsInstance(inky_target, tuple)
        clyde.x, clyde.y = 10.0, 10.0
        self.assertEqual(engine._get_ghost_target(clyde), (2.0, 2.0))

    def test_get_ghost_target_clyde_scatters(self) -> None:
        """Test Clyde scatters when close to the player."""
        engine = make_engine()
        clyde = engine.ghosts[3]
        clyde.x, clyde.y = 2.5, 2.5
        target = engine._get_ghost_target(clyde)
        self.assertEqual(target, (0.0, 4.0))

    def test_update_ghosts_initial_direction(self) -> None:
        """Test ghosts pick an initial open direction."""
        engine = make_engine()
        engine._update_ghosts(0.01)
        for ghost in engine.ghosts:
            self.assertNotEqual(ghost.dir, Direction.NONE)

    def test_update_ghosts_respawn(self) -> None:
        """Test eaten ghosts respawn after their timer."""
        engine = make_engine()
        ghost = engine.ghosts[0]
        ghost.is_eaten = True
        ghost.respawn_timer = 0.1
        ghost.x = 9.0
        engine._update_ghosts(0.2)
        self.assertFalse(ghost.is_eaten)
        self.assertEqual(ghost.x, 0.0)

    def test_update_ghosts_frightened_random(self) -> None:
        """Test frightened ghosts choose random valid exits."""
        engine = make_engine()
        ghost = engine.ghosts[0]
        ghost.x, ghost.y = 2.0, 2.0
        ghost.dir = Direction.RIGHT
        engine.frightened_timer = 1.0
        with patch("src.game.random.choice", return_value=Direction.DOWN):
            engine._update_ghosts(1.0)
        self.assertEqual(ghost.dir, Direction.DOWN)

    def test_update_ghosts_targeted(self) -> None:
        """Test normal ghosts choose a target-based direction."""
        engine = make_engine()
        ghost = engine.ghosts[0]
        ghost.x, ghost.y = 2.0, 2.0
        ghost.dir = Direction.RIGHT
        engine._update_ghosts(0.2)
        self.assertIn(
            ghost.dir,
            [Direction.UP, Direction.DOWN, Direction.RIGHT],
        )

    def test_update_ghosts_dead_end(self) -> None:
        """Test ghosts stop when no exit exists."""
        mazes = [open_maze() for _ in range(10)]
        mazes[0][1][1] = 0
        mazes[0][1][0] = 15
        mazes[0][0][1] = 15
        mazes[0][2][1] = 15
        mazes[0][1][2] = 15
        engine = GameEngine(make_config(), mazes)
        ghost = engine.ghosts[0]
        ghost.x, ghost.y = 0.99, 1.0
        ghost.dir = Direction.RIGHT
        engine._update_ghosts(0.1)
        self.assertEqual(ghost.dir, Direction.NONE)

    def test_check_item_consumption_pacgum(self) -> None:
        """Test eating a pacgum increases the score."""
        engine = make_engine()
        pos = (round(engine.player_x), round(engine.player_y))
        engine.pacgums = {pos}
        engine._check_item_consumption()
        self.assertEqual(engine.score, 10)
        self.assertEqual(len(engine.pacgums), 0)

    def test_check_item_consumption_super_pacgum(self) -> None:
        """Test eating a super pacgum triggers frightened mode."""
        engine = make_engine()
        pos = (round(engine.player_x), round(engine.player_y))
        engine.super_pacgums = {pos}
        engine._check_item_consumption()
        self.assertEqual(engine.score, 50)
        self.assertEqual(engine.frightened_timer, 7.0)

    def test_check_ghost_collisions_death(self) -> None:
        """Test collision with a normal ghost kills the player."""
        engine = make_engine(lives=3)
        ghost = engine.ghosts[0]
        ghost.x, ghost.y = engine.player_x, engine.player_y
        engine._check_ghost_collisions()
        self.assertEqual(engine.lives, 2)

    def test_check_ghost_collisions_invincible(self) -> None:
        """Test invincibility prevents death."""
        engine = make_engine(lives=3)
        engine.cheat_invincible = True
        ghost = engine.ghosts[0]
        ghost.x, ghost.y = engine.player_x, engine.player_y
        engine._check_ghost_collisions()
        self.assertEqual(engine.lives, 3)

    def test_check_ghost_collisions_eaten(self) -> None:
        """Test eating a frightened ghost adds points."""
        engine = make_engine()
        engine.frightened_timer = 1.0
        ghost = engine.ghosts[0]
        ghost.x, ghost.y = engine.player_x, engine.player_y
        engine._check_ghost_collisions()
        self.assertTrue(ghost.is_eaten)
        self.assertEqual(engine.score, 200)
        self.assertEqual(ghost.respawn_timer, 7.0)

    def test_check_ghost_collisions_far(self) -> None:
        """Test distant ghosts do not collide."""
        engine = make_engine()
        engine._check_ghost_collisions()
        self.assertEqual(engine.lives, 3)

    def test_handle_player_death_respawn(self) -> None:
        """Test death resets player and ghost positions."""
        engine = make_engine(lives=3)
        engine.player_x = 0.0
        engine.player_y = 0.0
        engine._handle_player_death("ghost")
        self.assertEqual(engine.lives, 2)
        self.assertEqual((engine.player_x, engine.player_y), (2.0, 2.0))
        self.assertEqual(engine.level_time_remaining, 100.0)

    def test_handle_player_death_game_over(self) -> None:
        """Test the last death ends the game."""
        engine = make_engine(lives=1)
        engine._handle_player_death("ghost")
        self.assertTrue(engine.is_game_over)
        self.assertEqual(engine.game_over_reason, "ghost")

    def test_advance_level_middle_and_victory(self) -> None:
        """Test advancing levels and final victory."""
        engine = make_engine()
        engine._advance_level()
        self.assertEqual(engine.current_level_idx, 1)
        engine.current_level_idx = len(engine.mazes) - 1
        engine._advance_level()
        self.assertTrue(engine.is_victory)

    def test_cheat_toggles(self) -> None:
        """Test cheat toggle methods."""
        engine = make_engine()
        self.assertTrue(engine.toggle_invincibility())
        self.assertTrue(engine.toggle_freeze_ghosts())
        self.assertTrue(engine.toggle_speed())
        self.assertFalse(engine.toggle_invincibility())

    def test_reset_cheats(self) -> None:
        """Test resetting all cheats."""
        engine = make_engine()
        engine.cheat_invincible = True
        engine.cheat_ghost_freeze = True
        engine.cheat_speed_boost = True
        engine.reset_cheats()
        self.assertFalse(engine.cheat_invincible)
        self.assertFalse(engine.cheat_ghost_freeze)
        self.assertFalse(engine.cheat_speed_boost)

    def test_add_extra_life(self) -> None:
        """Test granting an extra life."""
        engine = make_engine()
        self.assertEqual(engine.add_extra_life(), 4)

    def test_add_extra_life_clamped(self) -> None:
        """Test extra lives are clamped at the maximum."""
        engine = make_engine()
        engine.lives = engine.max_lives
        with patch("builtins.print") as mocked_print:
            result = engine.add_extra_life()
            mocked_print.assert_called_once()
        self.assertEqual(result, engine.max_lives)

    def test_skip_level(self) -> None:
        """Test skipping advances the level."""
        engine = make_engine()
        engine.skip_level()
        self.assertEqual(engine.current_level_idx, 1)

    def test_trigger_frightened(self) -> None:
        """Test manually triggering frightened mode."""
        engine = make_engine()
        engine.trigger_frightened()
        self.assertEqual(engine.frightened_timer,
                         engine.frightened_duration)

    def test_add_score_bonus(self) -> None:
        """Test adding bonus score."""
        engine = make_engine()
        self.assertEqual(engine.add_score_bonus(), 1000)
        self.assertEqual(engine.add_score_bonus(500), 1500)


if __name__ == "__main__":
    unittest.main()
