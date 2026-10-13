"""Graphical user interface and rendering engine for Pac-Man using Pygame.

Handles Main Menu, In-game View & HUD, Pause Menu, Highscores screen,
Cheat hotkeys, and Game Over / Victory name entry.
"""

import math
from pathlib import Path
from typing import List, Tuple
import pygame

from src.parser import Pacman_Parser
from src.game import GameEngine, Direction
from src.highscore import HighscoreManager


COLOR_DARK_BLUE = (23, 23, 168)
COLOR_PACMAN_BLUE = (0, 0, 255)
COLOR_YELLOW = (255, 255, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_GRAY = (150, 150, 150)
COLOR_FRIGHTENED_GHOST = (64, 64, 255)
COLOR_GHOST_BLINK = (255, 255, 255)
FRIGHTENED_BLINK_THRESHOLD = 2.0
COLOR_GREEN = (0, 255, 0)
COLOR_RED = (255, 50, 50)

FONT_PATH = (Path(__file__).parent.parent / "assets" / "fonts"
             / "PressStart2P-Regular.ttf")


class Renderer:
    """Renders Pac-Man gameplay, HUD, menus, and handles user input."""

    def __init__(self, config: Pacman_Parser,
                 mazes: List[List[List[int]]]) -> None:
        pygame.init()
        info = pygame.display.Info()
        self.screen_x = info.current_w
        self.screen_y = info.current_h
        self.screen = pygame.display.set_mode(
            (self.screen_x, self.screen_y), pygame.FULLSCREEN
        )
        pygame.display.set_caption("Pac-Man")

        self.config = config
        self.mazes = mazes
        self.reloj = pygame.time.Clock()

        self.highscore_mgr = HighscoreManager(config.highscore_filename)
        self.engine = GameEngine(config, mazes)

        # UI States: 'menu', 'game', 'pause', 'highscores', 'instructions'
        self.state = "menu"
        self.menu_selection = 0
        self.pause_selection = 0
        self.playing = True

        # End game player name input
        self.player_name_input = ""
        self.score_saved = False

        # Cheat feedback message
        self.cheat_message = ""
        self.cheat_message_timer = 0.0

    def _font(self, size: int) -> pygame.font.Font:
        if FONT_PATH.exists():
            return pygame.font.Font(str(FONT_PATH), size)
        return pygame.font.SysFont("Arial", size)

    def _set_cheat_msg(self, msg: str) -> None:
        self.cheat_message = msg
        self.cheat_message_timer = 2.5

    def _draw_pacman_sprite(self, center: Tuple[int, int],
                            radius: int,
                            direction: Tuple[int, int] = Direction.RIGHT
                            ) -> None:
        dx, dy = direction
        if dx == 0 and dy == -1:   # UP
            rotation = 90
        elif dx == 0 and dy == 1:  # DOWN
            rotation = 270
        elif dx == -1 and dy == 0:  # LEFT
            rotation = 180
        else:                      # RIGHT / NONE
            rotation = 0

        t = pygame.time.get_ticks() / 250.0
        mouth = 20 + 20 * (0.5 + 0.5 * math.sin(t))
        points = [center]
        for angle in range(int(rotation + mouth),
                           int(rotation + 360 - mouth) + 1, 10):
            rad = math.radians(angle)
            points.append(
                (
                    int(center[0] + radius * math.cos(rad)),
                    int(center[1] - radius * math.sin(rad)),
                )
            )
        pygame.draw.polygon(self.screen, COLOR_YELLOW, points)

    def _draw_ghost_sprite(
        self, center: Tuple[int, int], radius: int,
        color: Tuple[int, int, int]
    ) -> None:
        cx, cy = center
        pygame.draw.circle(self.screen, color, (cx, cy - radius // 4), radius)
        body_rect = pygame.Rect(cx - radius, cy - radius // 4,
                                radius * 2, radius)
        pygame.draw.rect(self.screen, color, body_rect)
        eye_offset = radius // 2
        eye_r = max(2, radius // 4)
        pygame.draw.circle(
            self.screen, COLOR_WHITE,
            (cx - eye_offset, cy - radius // 3), eye_r
        )
        pygame.draw.circle(
            self.screen, COLOR_WHITE,
            (cx + eye_offset, cy - radius // 3), eye_r
        )

    def draw_maze_and_entities(self) -> None:
        maze = self.engine.maze
        h = len(maze)
        w = len(maze[0]) if maze else 0
        if w == 0 or h == 0:
            return

        hud_height = 80
        avail_h = self.screen_y - hud_height
        cell = min(self.screen_x / w, avail_h / h) * 0.92

        ox = (self.screen_x - cell * w) / 2
        oy = hud_height + (avail_h - cell * h) / 2

        # 1. Draw Walls
        for y, row in enumerate(maze):
            for x, val in enumerate(row):
                px = ox + x * cell
                py = oy + y * cell
                if val == 15:
                    pygame.draw.rect(self.screen, COLOR_DARK_BLUE,
                                     (px, py, cell, cell))
                    continue
                line_w = max(2, int(cell * 0.1))
                if val & 1:  # North
                    pygame.draw.line(
                        self.screen, COLOR_DARK_BLUE,
                        (px, py), (px + cell, py), line_w
                    )
                if val & 2:  # East
                    pygame.draw.line(
                        self.screen, COLOR_DARK_BLUE,
                        (px + cell, py), (px + cell, py + cell), line_w
                    )
                if val & 4:  # South
                    pygame.draw.line(
                        self.screen, COLOR_DARK_BLUE,
                        (px, py + cell), (px + cell, py + cell), line_w
                    )
                if val & 8:  # West
                    pygame.draw.line(
                        self.screen, COLOR_DARK_BLUE,
                        (px, py), (px, py + cell), line_w
                    )

        # 2. Draw Pacgums (dots)
        dot_r = max(2, int(cell * 0.12))
        for px_cell, py_cell in self.engine.pacgums:
            cx = int(ox + (px_cell + 0.5) * cell)
            cy = int(oy + (py_cell + 0.5) * cell)
            pygame.draw.circle(self.screen, COLOR_WHITE, (cx, cy), dot_r)

        # 3. Draw Super-pacgums
        t = pygame.time.get_ticks() / 200.0
        pulse = 0.8 + 0.3 * math.sin(t)
        super_r = max(4, int(cell * 0.3 * pulse))
        for spx, spy in self.engine.super_pacgums:
            cx = int(ox + (spx + 0.5) * cell)
            cy = int(oy + (spy + 0.5) * cell)
            pygame.draw.circle(self.screen, COLOR_YELLOW, (cx, cy), super_r)

        # 4. Draw Pac-Man
        pcx = int(ox + (self.engine.player_x + 0.5) * cell)
        pcy = int(oy + (self.engine.player_y + 0.5) * cell)
        pac_r = max(6, int(cell * 0.38))
        self._draw_pacman_sprite((pcx, pcy), pac_r,
                                 self.engine.player_dir)

        # 5. Draw Ghosts
        for ghost in self.engine.ghosts:
            if ghost.is_eaten:
                continue
            gcx = int(ox + (ghost.x + 0.5) * cell)
            gcy = int(oy + (ghost.y + 0.5) * cell)
            g_r = max(6, int(cell * 0.38))
            if self.engine.frightened_timer > 0:
                if self.engine.frightened_timer <= FRIGHTENED_BLINK_THRESHOLD:
                    on = (pygame.time.get_ticks() // 200) % 2 == 0
                    color = COLOR_GHOST_BLINK if on else COLOR_FRIGHTENED_GHOST
                else:
                    color = COLOR_FRIGHTENED_GHOST
            else:
                color = ghost.color
            self._draw_ghost_sprite((gcx, gcy), g_r, color)

    def draw_hud(self) -> None:
        """Render in-game HUD (Chapter VI.8): Score, Lives, Level, Time."""
        hud_font = self._font(18)

        score_text = f"SCORE: {self.engine.score}"
        lives_text = f"LIVES: {self.engine.lives}"
        lvl_num = self.engine.current_level_idx + 1
        lvl_text = f"LEVEL: {lvl_num}/{len(self.mazes)}"
        time_text = f"TIME: {int(max(0, self.engine.level_time_remaining))}s"

        surf_score = hud_font.render(score_text, True, COLOR_WHITE)
        surf_lives = hud_font.render(lives_text, True, COLOR_RED)
        surf_lvl = hud_font.render(lvl_text, True, COLOR_YELLOW)
        surf_time = hud_font.render(time_text, True, COLOR_GREEN)

        self.screen.blit(surf_score, (30, 25))
        self.screen.blit(surf_lives, (int(self.screen_x * 0.3), 25))
        self.screen.blit(surf_lvl, (int(self.screen_x * 0.55), 25))
        self.screen.blit(surf_time, (int(self.screen_x * 0.8), 25))

        # Active cheat indicators (Chapter VI.5)
        active_badges = []
        if self.engine.cheat_invincible:
            active_badges.append("INVINCIBLE")
        if self.engine.cheat_ghost_freeze:
            active_badges.append("FREEZE")
        if self.engine.cheat_speed_boost:
            active_badges.append("SPEEDx2")

        badge_font = self._font(12)
        if active_badges:
            badge_str = "[CHEATS ACTIVE: " + " | ".join(active_badges) + "]"
            badge_surf = badge_font.render(badge_str, True, COLOR_YELLOW)
            self.screen.blit(badge_surf, (30, 52))

        if self.cheat_message_timer > 0:
            msg_font = self._font(12)
            msg_surf = msg_font.render(
                f">> {self.cheat_message}", True, COLOR_GREEN
            )
            y_offset = 68 if active_badges else 52
            self.screen.blit(msg_surf, (30, y_offset))

    def _draw_menu(self) -> None:
        """Main Menu: Start Game, View Highscores, Instructions, Exit."""
        self.screen.fill(COLOR_BLACK)

        title_font = self._font(72)
        title = title_font.render("PAC-MAN", True, COLOR_YELLOW)
        title_rect = title.get_rect(
            center=(self.screen_x // 2, int(self.screen_y * 0.18))
        )
        self.screen.blit(title, title_rect)
        self._draw_pacman_sprite((title_rect.left - 60,
                                  title_rect.centery), 40)

        options = ["START GAME", "HIGHSCORES", "INSTRUCTIONS", "EXIT"]
        btn_font = self._font(22)

        start_y = int(self.screen_y * 0.38)
        gap = int(self.screen_y * 0.11)

        for i, opt in enumerate(options):
            rect = pygame.Rect(0, 0, 420, 65)
            rect.center = (self.screen_x // 2, start_y + i * gap)
            selected = i == self.menu_selection

            if selected:
                pygame.draw.rect(self.screen, COLOR_YELLOW,
                                 rect, border_radius=10)
                txt_col = COLOR_BLACK
            else:
                pygame.draw.rect(
                    self.screen, COLOR_PACMAN_BLUE, rect,
                    width=3, border_radius=10
                )
                txt_col = COLOR_WHITE

            txt = btn_font.render(opt, True, txt_col)
            txt_rect = txt.get_rect(center=rect.center)
            self.screen.blit(txt, txt_rect)

        help_font = self._font(14)
        help_txt = help_font.render(
            "UP/DOWN: SELECT | ENTER/SPACE: CONFIRM | ESC: QUIT",
            True, COLOR_GRAY
        )
        self.screen.blit(
            help_txt,
            help_txt.get_rect(center=(self.screen_x // 2,
                                      self.screen_y - 30))
        )

    def _draw_highscores_screen(self) -> None:
        self.screen.fill(COLOR_BLACK)
        title_font = self._font(42)
        title = title_font.render("TOP 10 HIGHSCORES", True, COLOR_YELLOW)
        self.screen.blit(
            title,
            title.get_rect(center=(self.screen_x // 2,
                                   int(self.screen_y * 0.15)))
        )

        scores = self.highscore_mgr.get_top_scores()
        row_font = self._font(18)
        start_y = int(self.screen_y * 0.28)
        gap = int(self.screen_y * 0.055)

        if not scores:
            empty_txt = row_font.render(
                "NO HIGHSCORES RECORDED YET", True, COLOR_GRAY
            )
            self.screen.blit(
                empty_txt,
                empty_txt.get_rect(center=(self.screen_x // 2, start_y + 60))
            )
        else:
            for idx, entry in enumerate(scores):
                rank = f"{idx + 1:2d}."
                name = entry["name"]
                sc = f"{entry['score']} PTS"
                row_str = f"{rank}  {name:<10}   {sc:>10}"
                surf = row_font.render(row_str, True, COLOR_WHITE)
                self.screen.blit(
                    surf,
                    surf.get_rect(center=(self.screen_x // 2,
                                          start_y + idx * gap)),
                )

        back_font = self._font(16)
        back_txt = back_font.render(
            "PRESS ESC TO RETURN TO MENU", True, COLOR_YELLOW
        )
        self.screen.blit(
            back_txt,
            back_txt.get_rect(center=(self.screen_x // 2,
                                      self.screen_y - 50)),
        )

    def _draw_instructions_screen(self) -> None:
        self.screen.fill(COLOR_BLACK)
        title_font = self._font(42)
        title = title_font.render("INSTRUCTIONS", True, COLOR_YELLOW)
        self.screen.blit(
            title,
            title.get_rect(center=(self.screen_x // 2,
                                   int(self.screen_y * 0.15)))
        )

        lines = [
            "- Controls: Arrow Keys or WASD to navigate corridors",
            "- P: Pause / Resume game",
            "- Pacgums: Collect all small dots to advance to next level",
            "- Super Pacgums: Corner power pellets allow eating ghosts",
            "- Avoid ghosts unless powered up!",
            "",
            "CHEATS (For Evaluation - Chapter VI.5):",
            "- [1] Toggle Invincibility",
            "- [2] Freeze Ghosts",
            "- [3] Extra Life (+1)",
            "- [4] Toggle Speed Boost",
            "- [5] Skip Level",
            "- [6] Trigger Edible Ghosts (Frightened Mode)",
            "- [7] Bonus Score (+1000 PTS)",
        ]
        body_font = self._font(15)
        start_y = int(self.screen_y * 0.28)
        gap = int(self.screen_y * 0.045)

        for i, line in enumerate(lines):
            col = (COLOR_YELLOW if "CHEAT" in line or "[" in line
                   else COLOR_WHITE)
            surf = body_font.render(line, True, col)
            self.screen.blit(
                surf,
                surf.get_rect(center=(self.screen_x // 2, start_y + i * gap)),
            )

        back_font = self._font(16)
        back_txt = back_font.render(
            "PRESS ESC TO RETURN TO MENU", True, COLOR_YELLOW
        )
        self.screen.blit(
            back_txt,
            back_txt.get_rect(center=(self.screen_x // 2,
                                      self.screen_y - 50)),
        )

    def _draw_pause_menu(self) -> None:
        overlay = pygame.Surface(
            (self.screen_x, self.screen_y), pygame.SRCALPHA
        )
        overlay.fill((0, 0, 0, 190))
        self.screen.blit(overlay, (0, 0))

        title_font = self._font(48)
        title = title_font.render("PAUSED", True, COLOR_YELLOW)
        self.screen.blit(
            title,
            title.get_rect(center=(self.screen_x // 2,
                                   int(self.screen_y * 0.3)))
        )

        options = ["RESUME GAME", "RETURN TO MAIN MENU"]
        btn_font = self._font(20)

        for i, opt in enumerate(options):
            selected = i == self.pause_selection
            rect = pygame.Rect(0, 0, 420, 60)
            rect.center = (
                self.screen_x // 2,
                int(self.screen_y * (0.48 + i * 0.12))
            )

            if selected:
                pygame.draw.rect(self.screen, COLOR_YELLOW,
                                 rect, border_radius=8)
                color = COLOR_BLACK
            else:
                pygame.draw.rect(
                    self.screen, COLOR_PACMAN_BLUE, rect,
                    width=3, border_radius=8
                )
                color = COLOR_WHITE

            txt = btn_font.render(opt, True, color)
            self.screen.blit(txt, txt.get_rect(center=rect.center))

    def _draw_endgame_screen(self) -> None:
        self.screen.fill(COLOR_BLACK)

        title_font = self._font(52)
        if self.engine.is_victory:
            msg = "VICTORY! YOU BEAT PAC-MAN!"
            color = COLOR_YELLOW
        else:
            msg = "GAME OVER"
            color = COLOR_RED

        title = title_font.render(msg, True, color)
        self.screen.blit(
            title,
            title.get_rect(center=(self.screen_x // 2,
                                   int(self.screen_y * 0.25)))
        )

        score_font = self._font(26)
        score_surf = score_font.render(
            f"FINAL SCORE: {self.engine.score}", True, COLOR_WHITE
        )
        self.screen.blit(
            score_surf,
            score_surf.get_rect(center=(self.screen_x // 2,
                                        int(self.screen_y * 0.38))),
        )

        if not self.score_saved:
            prompt_font = self._font(18)
            prompt = prompt_font.render(
                "ENTER YOUR NAME (MAX 10):", True, COLOR_WHITE
            )
            self.screen.blit(
                prompt,
                prompt.get_rect(
                    center=(self.screen_x // 2, int(self.screen_y * 0.50))
                ),
            )

            box_rect = pygame.Rect(0, 0, 360, 60)
            box_rect.center = (self.screen_x // 2, int(self.screen_y * 0.58))
            pygame.draw.rect(self.screen, COLOR_PACMAN_BLUE, box_rect, width=3)
            cursor = "_" if (pygame.time.get_ticks() // 400) % 2 == 0 else ""
            display_name = self.player_name_input + cursor
            name_surf = score_font.render(display_name, True, COLOR_YELLOW)
            self.screen.blit(name_surf,
                             name_surf.get_rect(center=box_rect.center))

            confirm_txt = prompt_font.render(
                "PRESS ENTER TO SAVE HIGHSCORE", True, COLOR_GRAY
            )
            self.screen.blit(
                confirm_txt,
                confirm_txt.get_rect(
                    center=(self.screen_x // 2, int(self.screen_y * 0.68))
                ),
            )
        else:
            saved_font = self._font(20)
            saved_txt = saved_font.render(
                "SCORE SAVED! PRESS ENTER OR ESC FOR MAIN MENU",
                True, COLOR_GREEN
            )
            self.screen.blit(
                saved_txt,
                saved_txt.get_rect(
                    center=(self.screen_x // 2, int(self.screen_y * 0.58))
                ),
            )

    def _start_new_game(self) -> None:
        self.engine = GameEngine(self.config, self.mazes)
        self.state = "game"
        self.player_name_input = ""
        self.score_saved = False

    def _handle_keydown(self, event: pygame.event.Event) -> None:
        key = event.key

        if self.state == "menu":
            if key in (pygame.K_UP, pygame.K_w):
                self.menu_selection = (self.menu_selection - 1) % 4
            elif key in (pygame.K_DOWN, pygame.K_s):
                self.menu_selection = (self.menu_selection + 1) % 4
            elif key in (pygame.K_RETURN, pygame.K_SPACE):
                if self.menu_selection == 0:
                    self._start_new_game()
                elif self.menu_selection == 1:
                    self.state = "highscores"
                elif self.menu_selection == 2:
                    self.state = "instructions"
                elif self.menu_selection == 3:
                    self.playing = False
            elif key == pygame.K_ESCAPE:
                self.playing = False

        elif self.state in ("highscores", "instructions"):
            if key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                self.state = "menu"

        elif self.state == "game":
            if key in (pygame.K_p, pygame.K_ESCAPE):
                self.state = "pause"
                self.pause_selection = 0
            elif key in (pygame.K_UP, pygame.K_w):
                self.engine.request_player_direction(Direction.UP)
            elif key in (pygame.K_RIGHT, pygame.K_d):
                self.engine.request_player_direction(Direction.RIGHT)
            elif key in (pygame.K_DOWN, pygame.K_s):
                self.engine.request_player_direction(Direction.DOWN)
            elif key in (pygame.K_LEFT, pygame.K_a):
                self.engine.request_player_direction(Direction.LEFT)

            # Cheat shortcuts (Chapter VI.5)
            elif key == pygame.K_1:
                inv = self.engine.toggle_invincibility()
                self._set_cheat_msg(f"Invincibility {'ON' if inv else 'OFF'}")
            elif key == pygame.K_2:
                frz = self.engine.toggle_freeze_ghosts()
                self._set_cheat_msg(f"Ghost Freeze {'ON' if frz else 'OFF'}")
            elif key == pygame.K_3:
                lives = self.engine.add_extra_life()
                self._set_cheat_msg(f"Added +1 Life (Total: {lives})")
            elif key == pygame.K_4:
                spd = self.engine.toggle_speed()
                self._set_cheat_msg(f"Speed Boost {'ON' if spd else 'OFF'}")
            elif key == pygame.K_5:
                self.engine.skip_level()
                self._set_cheat_msg("Skipped to Next Level!")
            elif key == pygame.K_6:
                self.engine.trigger_frightened()
                self._set_cheat_msg("Ghosts are now Edible (Power Mode)!")
            elif key == pygame.K_7:
                pts = self.engine.add_score_bonus(1000)
                self._set_cheat_msg(f"+1000 Score Bonus (Total: {pts})")

        elif self.state == "pause":
            if key in (pygame.K_UP, pygame.K_w):
                self.pause_selection = (self.pause_selection - 1) % 2
            elif key in (pygame.K_DOWN, pygame.K_s):
                self.pause_selection = (self.pause_selection + 1) % 2
            elif key in (pygame.K_RETURN, pygame.K_SPACE):
                if self.pause_selection == 0:
                    self.state = "game"
                else:
                    self.state = "menu"
            elif key in (pygame.K_p, pygame.K_ESCAPE):
                self.state = "game"

        elif self.state == "endgame":
            if not self.score_saved:
                if key == pygame.K_RETURN:
                    self.highscore_mgr.add_score(
                        self.player_name_input, self.engine.score
                    )
                    self.score_saved = True
                elif key == pygame.K_BACKSPACE:
                    self.player_name_input = self.player_name_input[:-1]
                else:
                    char = event.unicode
                    if char.isalnum() or char == " ":
                        if len(self.player_name_input) < 10:
                            self.player_name_input += char.upper()
            else:
                if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                    self.state = "menu"

    def run(self) -> None:
        """Main game application loop."""
        self.playing = True
        while self.playing:
            dt = self.reloj.tick(30) / 1000.0

            if self.cheat_message_timer > 0:
                self.cheat_message_timer = max(
                    0.0, self.cheat_message_timer - dt
                )

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.playing = False
                elif event.type == pygame.KEYDOWN:
                    self._handle_keydown(event)

            if self.state == "menu":
                self._draw_menu()
            elif self.state == "highscores":
                self._draw_highscores_screen()
            elif self.state == "instructions":
                self._draw_instructions_screen()
            elif self.state == "game":
                self.engine.update(dt)
                if self.engine.is_game_over or self.engine.is_victory:
                    self.state = "endgame"
                self.screen.fill(COLOR_BLACK)
                self.draw_maze_and_entities()
                self.draw_hud()
            elif self.state == "pause":
                self.screen.fill(COLOR_BLACK)
                self.draw_maze_and_entities()
                self.draw_hud()
                self._draw_pause_menu()
            elif self.state == "endgame":
                self._draw_endgame_screen()

            pygame.display.flip()

        self.cleanup()

    def cleanup(self) -> None:
        """Cleanly tear down Pygame resources."""
        pygame.quit()
