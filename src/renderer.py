import math
import sys
from pathlib import Path
import pygame
from src.parser import Pacman_Parser


AZUL_OSCURO = (23, 23, 168)
AZUL_PACMAN = (0, 0, 255)
AMARILLO = (255, 255, 0)
BLANCO = (255, 255, 255)
NEGRO = (0, 0, 0)

FONT_PATH = Path(__file__).parent.parent / "assets" / "fonts" / \
    "PressStart2P-Regular.ttf"


class Renderer():
    def __init__(self, config: Pacman_Parser,
                 maze: list[list[int]]) -> None:
        pygame.init()

        info = pygame.display.Info()
        self.screen_x = info.current_w
        self.screen_y = info.current_h
        self.screen = pygame.display.set_mode((self.screen_x, self.screen_y),
                                              pygame.FULLSCREEN)
        pygame.display.set_caption("pac-man")

        self.config = config
        self.maze = maze

        self.reloj = pygame.time.Clock()
        self.playing = False
        self.state = "menu"
        self.menu_selection = 0

    def _font(self, size: int) -> pygame.font.Font:
        if FONT_PATH.exists():
            return pygame.font.Font(str(FONT_PATH), size)
        return pygame.font.SysFont("Arial", size)

    def draw_maze(self, maze: list[list[int]]) -> None:
        height = len(maze)
        width = len(maze[0]) if maze else 0
        if width == 0:
            return
        cell = min(self.screen_x / width, self.screen_y / height)
        ox = (self.screen_x - cell * width) / 2
        oy = (self.screen_y - cell * height) / 2
        for y, row in enumerate(maze):
            for x, value in enumerate(row):
                px = ox + x * cell
                py = oy + y * cell
                if value == 15:
                    pygame.draw.rect(self.screen, AZUL_OSCURO,
                                     (px, py, cell, cell))
                    continue
                if value & 1:
                    pygame.draw.line(self.screen, AZUL_OSCURO,
                                     (px, py), (px + cell, py), 4)
                if value & 2:
                    pygame.draw.line(self.screen, AZUL_OSCURO,
                                     (px + cell, py),
                                     (px + cell, py + cell), 4)
                if value & 4:
                    pygame.draw.line(self.screen, AZUL_OSCURO,
                                     (px, py + cell),
                                     (px + cell, py + cell), 4)
                if value & 8:
                    pygame.draw.line(self.screen, AZUL_OSCURO,
                                     (px, py), (px, py + cell), 4)

    def _draw_pacman(self, center: tuple[int, int], radius: int) -> None:
        t = pygame.time.get_ticks() / 300.0
        mouth = 20 + 20 * (0.5 + 0.5 * math.sin(t))
        points = [center]
        for angle in range(int(mouth), int(360 - mouth) + 1, 5):
            rad = math.radians(angle)
            points.append((int(center[0] + radius * math.cos(rad)),
                           int(center[1] - radius * math.sin(rad))))
        pygame.draw.polygon(self.screen, AMARILLO, points)

    def _draw_menu(self) -> None:
        self.screen.fill(NEGRO)

        title_font = self._font(110)
        title = title_font.render("PAC-MAN", True, AMARILLO)
        title_rect = title.get_rect(
            center=(self.screen_x // 2, int(self.screen_y * 0.22)))
        self.screen.blit(title, title_rect)

        self._draw_pacman((title_rect.left - 100, title_rect.centery), 60)

        buttons = ["START GAME", "EXIT"]
        button_font = self._font(32)

        for index, label in enumerate(buttons):
            selected = index == self.menu_selection
            center_y = int(self.screen_y * (0.52 + index * 0.18))
            rect = pygame.Rect(0, 0, 460, 90)
            rect.center = (self.screen_x // 2, center_y)

            if selected:
                pygame.draw.rect(self.screen, AMARILLO, rect,
                                 border_radius=12)
                color = NEGRO
            else:
                pygame.draw.rect(self.screen, AZUL_PACMAN, rect, width=4,
                                 border_radius=12)
                color = BLANCO

            text = button_font.render(label, True, color)
            text_rect = text.get_rect(center=rect.center)
            self.screen.blit(text, text_rect)

        help_text = ("FLECHAS: NAVEGAR   ENTER/ESPACIO: SELECCIONAR   "
                     "ESC: SALIR")
        help_font = self._font(24)
        help_surface = help_font.render(help_text, True, BLANCO)
        help_rect = help_surface.get_rect(
            bottomleft=(20, self.screen_y - 20))
        self.screen.blit(help_surface, help_rect)

    def _handle_key(self, key: int) -> None:
        if self.state == "menu":
            if key == pygame.K_UP:
                self.menu_selection = (self.menu_selection - 1) % 2
            elif key == pygame.K_DOWN:
                self.menu_selection = (self.menu_selection + 1) % 2
            elif key == pygame.K_RETURN or key == pygame.K_SPACE:
                if self.menu_selection == 0:
                    self.state = "game"
                else:
                    self.playing = False
            elif key == pygame.K_ESCAPE:
                self.playing = False
        else:
            if key == pygame.K_ESCAPE:
                self.state = "menu"

    def main_menu(self) -> None:
        """Este método arranca y mantiene el bucle principal del juego."""
        self.playing = True
        while self.playing:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    self.playing = False
                elif evento.type == pygame.KEYDOWN:
                    self._handle_key(evento.key)

            if self.state == "menu":
                self._draw_menu()
            else:
                self.screen.fill(NEGRO)
                self.draw_maze(self.maze)

            pygame.display.update()

            self.reloj.tick(24)
        self.final_cleanup()

    def final_cleanup(self) -> None:
        pygame.quit()
        try:
            sys.exit()
        except SystemExit:
            pass
