"""Unit tests for the pygame renderer module."""

import os
import tempfile
import unittest
from pathlib import Path
from typing import List
from unittest.mock import patch

import pygame

from src.game import Direction
from src.parser import Pacman_Parser
from src.renderer import Renderer

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")


def make_config() -> Pacman_Parser:
    """Build a valid parser configuration for renderer tests."""
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
            "highscore_filename": "renderer_scores.json",
            "lives": 3,
            "points_per_pacgum": 10,
            "points_per_super_pacgum": 50,
            "points_per_ghost": 200,
            "levels": levels,
        }
    )


def make_mazes() -> List[List[List[int]]]:
    """Build open mazes for renderer tests."""
    return [[[0 for _ in range(5)] for _ in range(5)]
            for _ in range(10)]


class TestRenderer(unittest.TestCase):
    """Tests for the Renderer class."""

    def setUp(self) -> None:
        """Create a renderer with a temporary working directory."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.previous_cwd = os.getcwd()
        os.chdir(self.temp_dir.name)
        self.addCleanup(os.chdir, self.previous_cwd)
        self.config = make_config()
        self.mazes = make_mazes()
        self.renderer = Renderer(self.config, self.mazes)
        self.addCleanup(pygame.quit)

    def press(self, key: int, unicode: str = "") -> None:
        """Send a keydown event to the renderer."""
        event = pygame.event.Event(
            pygame.KEYDOWN, key=key, unicode=unicode
        )
        self.renderer._handle_keydown(event)

    def test_init_state(self) -> None:
        """Test initial renderer state."""
        self.assertEqual(self.renderer.state, "menu")
        self.assertEqual(self.renderer.menu_selection, 0)
        self.assertTrue(self.renderer.playing)
        self.assertFalse(self.renderer.score_saved)

    def test_font_existing_and_fallback(self) -> None:
        """Test font loading with and without the asset file."""
        self.assertIsNotNone(self.renderer._font(20))
        missing = Path("missing-font.ttf")
        with patch("src.renderer.FONT_PATH", missing):
            self.assertIsNotNone(self.renderer._font(20))

    def test_set_cheat_msg(self) -> None:
        """Test cheat message assignment."""
        self.renderer._set_cheat_msg("hello")
        self.assertEqual(self.renderer.cheat_message, "hello")
        self.assertEqual(self.renderer.cheat_message_timer, 2.5)

    def test_draw_pacman_sprite_directions(self) -> None:
        """Test Pac-Man sprite rotation for every direction."""
        for direction in (
            Direction.UP,
            Direction.DOWN,
            Direction.LEFT,
            Direction.RIGHT,
            Direction.NONE,
        ):
            self.renderer._draw_pacman_sprite((100, 100), 10, direction)

    def test_draw_ghost_sprite(self) -> None:
        """Test ghost sprite drawing."""
        self.renderer._draw_ghost_sprite((100, 100), 10, (255, 0, 0))

    def test_draw_maze_and_entities(self) -> None:
        """Test drawing the maze, food, player and ghosts."""
        self.renderer.draw_maze_and_entities()

    def test_draw_maze_and_entities_empty(self) -> None:
        """Test drawing an empty maze returns early."""
        self.renderer.engine.maze = []
        self.renderer.draw_maze_and_entities()

    def test_draw_maze_and_entities_ghost_states(self) -> None:
        """Test frightened, blinking and eaten ghost rendering."""
        self.renderer.engine.frightened_timer = 5.0
        self.renderer.draw_maze_and_entities()
        self.renderer.engine.frightened_timer = 1.0
        self.renderer.draw_maze_and_entities()
        self.renderer.engine.ghosts[0].is_eaten = True
        self.renderer.draw_maze_and_entities()

    def test_draw_hud(self) -> None:
        """Test HUD rendering with cheats and messages."""
        self.renderer.engine.cheat_invincible = True
        self.renderer.engine.cheat_ghost_freeze = True
        self.renderer.engine.cheat_speed_boost = True
        self.renderer.cheat_message = "test"
        self.renderer.cheat_message_timer = 1.0
        self.renderer.draw_hud()

    def test_draw_hud_without_cheats(self) -> None:
        """Test HUD rendering without active cheats."""
        self.renderer.draw_hud()

    def test_draw_action_bar(self) -> None:
        """Test action bar rendering in both modes."""
        self.renderer._draw_action_bar()
        self.renderer.cheat_mode_enabled = True
        self.renderer._draw_action_bar()

    def test_draw_menu(self) -> None:
        """Test main menu rendering."""
        self.renderer._draw_menu()

    def test_draw_highscores_screen(self) -> None:
        """Test highscores rendering with and without entries."""
        self.renderer._draw_highscores_screen()
        self.renderer.highscore_mgr.add_score("alice", 100)
        self.renderer._draw_highscores_screen()

    def test_draw_instructions_screen(self) -> None:
        """Test instructions screen rendering."""
        self.renderer._draw_instructions_screen()

    def test_draw_pause_menu(self) -> None:
        """Test pause menu rendering."""
        self.renderer._draw_pause_menu()

    def test_draw_endgame_screen_victory(self) -> None:
        """Test victory endgame rendering."""
        self.renderer.engine.is_victory = True
        self.renderer._draw_endgame_screen()

    def test_draw_endgame_screen_timeout(self) -> None:
        """Test timeout game over rendering."""
        self.renderer.engine.is_victory = False
        self.renderer.engine.game_over_reason = "timeout"
        self.renderer._draw_endgame_screen()

    def test_draw_endgame_screen_ghost(self) -> None:
        """Test ghost game over rendering."""
        self.renderer.engine.game_over_reason = "ghost"
        self.renderer._draw_endgame_screen()

    def test_draw_endgame_screen_unknown_reason(self) -> None:
        """Test game over rendering with unknown reason."""
        self.renderer.engine.game_over_reason = "other"
        self.renderer._draw_endgame_screen()

    def test_draw_endgame_screen_saved(self) -> None:
        """Test endgame rendering after saving the score."""
        self.renderer.score_saved = True
        self.renderer._draw_endgame_screen()

    def test_start_new_game(self) -> None:
        """Test starting a new game resets renderer state."""
        self.renderer.player_name_input = "abc"
        self.renderer.score_saved = True
        self.renderer.cheat_mode_enabled = True
        self.renderer._start_new_game()
        self.assertEqual(self.renderer.state, "game")
        self.assertEqual(self.renderer.player_name_input, "")
        self.assertFalse(self.renderer.score_saved)
        self.assertFalse(self.renderer.cheat_mode_enabled)

    def test_menu_keydown_navigation(self) -> None:
        """Test main menu navigation keys."""
        self.press(pygame.K_DOWN)
        self.assertEqual(self.renderer.menu_selection, 1)
        self.press(pygame.K_s)
        self.assertEqual(self.renderer.menu_selection, 2)
        self.press(pygame.K_UP)
        self.assertEqual(self.renderer.menu_selection, 1)
        self.press(pygame.K_w)
        self.assertEqual(self.renderer.menu_selection, 0)

    def test_menu_keydown_actions(self) -> None:
        """Test main menu selection actions."""
        self.press(pygame.K_RETURN)
        self.assertEqual(self.renderer.state, "game")
        self.renderer.state = "menu"
        self.renderer.menu_selection = 1
        self.press(pygame.K_SPACE)
        self.assertEqual(self.renderer.state, "highscores")
        self.renderer.state = "menu"
        self.renderer.menu_selection = 2
        self.press(pygame.K_RETURN)
        self.assertEqual(self.renderer.state, "instructions")
        self.renderer.state = "menu"
        self.renderer.menu_selection = 3
        self.press(pygame.K_RETURN)
        self.assertFalse(self.renderer.playing)

    def test_menu_escape(self) -> None:
        """Test escaping the main menu quits the game."""
        self.press(pygame.K_ESCAPE)
        self.assertFalse(self.renderer.playing)

    def test_info_screens_return_to_menu(self) -> None:
        """Test highscores and instructions return to the menu."""
        self.renderer.state = "highscores"
        self.press(pygame.K_ESCAPE)
        self.assertEqual(self.renderer.state, "menu")
        self.renderer.state = "instructions"
        self.press(pygame.K_RETURN)
        self.assertEqual(self.renderer.state, "menu")

    def test_game_keydown_directions(self) -> None:
        """Test movement keys in game state."""
        self.renderer.state = "game"
        keys = [
            (pygame.K_UP, Direction.UP),
            (pygame.K_RIGHT, Direction.RIGHT),
            (pygame.K_DOWN, Direction.DOWN),
            (pygame.K_LEFT, Direction.LEFT),
        ]
        for key, direction in keys:
            self.press(key)
            self.assertEqual(self.renderer.engine.player_next_dir,
                             direction)

    def test_game_keydown_pause(self) -> None:
        """Test pausing the game."""
        self.renderer.state = "game"
        self.press(pygame.K_p)
        self.assertEqual(self.renderer.state, "pause")
        self.renderer.state = "game"
        self.press(pygame.K_ESCAPE)
        self.assertEqual(self.renderer.state, "pause")

    def test_game_cheat_mode_toggle(self) -> None:
        """Test toggling cheat mode on and off."""
        self.renderer.state = "game"
        self.press(pygame.K_c)
        self.assertTrue(self.renderer.cheat_mode_enabled)
        self.renderer.engine.cheat_invincible = True
        self.press(pygame.K_c)
        self.assertFalse(self.renderer.cheat_mode_enabled)
        self.assertFalse(self.renderer.engine.cheat_invincible)

    def test_game_cheat_shortcuts(self) -> None:
        """Test all cheat shortcuts while cheat mode is active."""
        self.renderer.state = "game"
        self.renderer.cheat_mode_enabled = True
        self.press(pygame.K_1)
        self.assertTrue(self.renderer.engine.cheat_invincible)
        self.press(pygame.K_2)
        self.assertTrue(self.renderer.engine.cheat_ghost_freeze)
        self.press(pygame.K_3)
        self.assertEqual(self.renderer.engine.lives, 4)
        self.press(pygame.K_4)
        self.assertTrue(self.renderer.engine.cheat_speed_boost)
        self.press(pygame.K_5)
        self.assertEqual(self.renderer.engine.current_level_idx, 1)
        self.press(pygame.K_6)
        self.assertGreater(self.renderer.engine.frightened_timer, 0.0)
        self.press(pygame.K_7)
        self.assertEqual(self.renderer.engine.score, 1000)

    def test_game_cheat_shortcuts_disabled(self) -> None:
        """Test cheat shortcuts are ignored without cheat mode."""
        self.renderer.state = "game"
        self.press(pygame.K_1)
        self.assertFalse(self.renderer.engine.cheat_invincible)

    def test_pause_keydown(self) -> None:
        """Test pause menu navigation and actions."""
        self.renderer.state = "pause"
        self.press(pygame.K_DOWN)
        self.assertEqual(self.renderer.pause_selection, 1)
        self.press(pygame.K_UP)
        self.assertEqual(self.renderer.pause_selection, 0)
        self.press(pygame.K_RETURN)
        self.assertEqual(self.renderer.state, "game")
        self.renderer.state = "pause"
        self.renderer.pause_selection = 1
        self.press(pygame.K_SPACE)
        self.assertEqual(self.renderer.state, "menu")
        self.renderer.state = "pause"
        self.press(pygame.K_p)
        self.assertEqual(self.renderer.state, "game")
        self.renderer.state = "pause"
        self.press(pygame.K_ESCAPE)
        self.assertEqual(self.renderer.state, "game")

    def test_endgame_name_entry(self) -> None:
        """Test entering a name and saving the score."""
        self.renderer.state = "endgame"
        self.press(pygame.K_a, "a")
        self.press(pygame.K_b, "b")
        self.assertEqual(self.renderer.player_name_input, "AB")
        self.press(pygame.K_BACKSPACE)
        self.assertEqual(self.renderer.player_name_input, "A")
        self.press(pygame.K_1, "!")
        self.assertEqual(self.renderer.player_name_input, "A")
        self.press(pygame.K_RETURN)
        self.assertTrue(self.renderer.score_saved)
        self.press(pygame.K_RETURN)
        self.assertEqual(self.renderer.state, "menu")

    def test_endgame_name_length_limit(self) -> None:
        """Test name entry caps at ten characters."""
        self.renderer.state = "endgame"
        for _ in range(12):
            self.press(pygame.K_a, "a")
        self.assertEqual(len(self.renderer.player_name_input), 10)

    def test_run_quits_on_quit_event(self) -> None:
        """Test the main loop exits on a quit event."""
        with patch("pygame.event.get",
                   return_value=[pygame.event.Event(pygame.QUIT)]):
            self.renderer.run()
        self.assertFalse(self.renderer.playing)

    def test_cleanup(self) -> None:
        """Test cleanup tears down pygame."""
        self.renderer.cleanup()


if __name__ == "__main__":
    unittest.main()
