"""Game domain model, state management, and entity logic for Pac-Man."""

import random
from typing import List, Tuple, Set
from src.parser import LevelConfig, Pacman_Parser


class Direction:
    """Movement directions."""
    NONE = (0, 0)
    UP = (0, -1)
    RIGHT = (1, 0)
    DOWN = (0, 1)
    LEFT = (-1, 0)

    OPPOSITES = {
        (0, -1): (0, 1),
        (0, 1): (0, -1),
        (-1, 0): (1, 0),
        (1, 0): (-1, 0),
        (0, 0): (0, 0),
    }


class Ghost:
    """Ghost entity with chase, scatter, edible, and respawn behaviors."""

    def __init__(self, ghost_id: int, start_x: int, start_y: int,
                 color: Tuple[int, int, int]) -> None:
        self.ghost_id = ghost_id
        self.start_pos = (start_x, start_y)
        self.x = float(start_x)
        self.y = float(start_y)
        self.color = color
        self.dir: Tuple[int, int] = Direction.NONE
        self.is_eaten = False
        self.respawn_timer = 0.0

    def reset_to_start(self) -> None:
        """Reset ghost to its corner spawn location."""
        self.x = float(self.start_pos[0])
        self.y = float(self.start_pos[1])
        self.dir = Direction.NONE
        self.is_eaten = False
        self.respawn_timer = 0.0


class GameEngine:
    """Coordinates gameplay logic, entities, and level progression."""

    def __init__(self, config: Pacman_Parser,
                 mazes: List[List[List[int]]]) -> None:
        self.config = config
        self.mazes = mazes
        self.current_level_idx = 0

        self.score = 0
        self.lives = config.lives

        # Cheat toggles
        self.cheat_invincible = False
        self.cheat_ghost_freeze = False
        self.cheat_speed_boost = False

        # Current level state
        self.maze: List[List[int]] = []
        self.grid_width = 0
        self.grid_height = 0
        self.level_time_remaining = 0.0

        # Entities
        self.player_x = 0.0
        self.player_y = 0.0
        self.player_spawn = (0, 0)
        self.player_dir: Tuple[int, int] = Direction.NONE
        self.player_next_dir: Tuple[int, int] = Direction.NONE

        self.ghosts: List[Ghost] = []
        self.frightened_timer = 0.0
        self.frightened_duration = 7.0

        # Pellets
        self.pacgums: Set[Tuple[int, int]] = set()
        self.super_pacgums: Set[Tuple[int, int]] = set()

        # Progression flags
        self.is_game_over = False
        self.is_victory = False
        self.level_completed = False

        self.load_level(0)

    @property
    def current_level_config(self) -> LevelConfig:
        return self.config.levels[self.current_level_idx]

    def load_level(self, level_idx: int) -> None:
        """Initialize state for a specified level index."""
        if level_idx >= len(self.mazes):
            self.is_victory = True
            return

        self.current_level_idx = level_idx
        lvl_cfg = self.current_level_config
        self.maze = self.mazes[level_idx]
        self.grid_height = len(self.maze)
        self.grid_width = len(self.maze[0]) if self.grid_height > 0 else 0
        self.level_time_remaining = float(lvl_cfg.level_max_time)
        self.frightened_timer = 0.0
        self.level_completed = False

        # 1. Player in the center (Chapter VI.1)
        cx = self.grid_width // 2
        cy = self.grid_height // 2
        self.player_spawn = (cx, cy)
        self.player_x = float(cx)
        self.player_y = float(cy)
        self.player_dir = Direction.NONE
        self.player_next_dir = Direction.NONE

        # 2. Ghosts in 4 corners (Chapter VI.1)
        corners = [
            (0, 0, (255, 0, 0)),
            (self.grid_width - 1, 0, (255, 184, 255)),
            (0, self.grid_height - 1, (0, 255, 255)),
            (self.grid_width - 1, self.grid_height - 1, (255, 184, 82)),
        ]
        self.ghosts = []
        for gid, (gx, gy, col) in enumerate(corners):
            self.ghosts.append(Ghost(gid, gx, gy, col))

        # 3. Super-pacgums in 4 corners (Chapter VI.1)
        self.super_pacgums = {
            (0, 0),
            (self.grid_width - 1, 0),
            (0, self.grid_height - 1),
            (self.grid_width - 1, self.grid_height - 1),
        }

        # 4. Pacgums in corridors (Chapter VI.1, VI.4)
        target_count = lvl_cfg.pacgum
        all_cells = [
            (x, y) for y in range(self.grid_height)
            for x in range(self.grid_width)
            if (x, y) not in self.super_pacgums and (x, y) != (cx, cy)
        ]
        if target_count <= 0 or target_count > len(all_cells):
            target_count = len(all_cells)

        random.seed(lvl_cfg.seed)
        chosen = random.sample(all_cells, min(target_count, len(all_cells)))
        self.pacgums = set(chosen)

    def can_move(self, x: int, y: int, direction: Tuple[int, int]) -> bool:
        """Check wall bitmask for movement from (x, y) in direction.

        Bits: 1=North wall, 2=East wall, 4=South wall, 8=West wall.
        """
        if not (0 <= x < self.grid_width and 0 <= y < self.grid_height):
            return False

        cell_val = self.maze[y][x]
        dx, dy = direction

        if dx == 0 and dy == -1:  # North / UP
            return (cell_val & 1) == 0
        if dx == 1 and dy == 0:   # East / RIGHT
            return (cell_val & 2) == 0
        if dx == 0 and dy == 1:   # South / DOWN
            return (cell_val & 4) == 0
        if dx == -1 and dy == 0:  # West / LEFT
            return (cell_val & 8) == 0

        return False

    def request_player_direction(self, direction: Tuple[int, int]) -> None:
        """Request a direction change for the player."""
        self.player_next_dir = direction

    def update(self, dt: float) -> None:
        """Advance game state by dt seconds."""
        if self.is_game_over or self.is_victory or self.level_completed:
            return

        # Countdown timer (Chapter VI.7)
        self.level_time_remaining -= dt
        if self.level_time_remaining <= 0.0:
            self._handle_player_death()
            return

        # Frightened timer
        if self.frightened_timer > 0.0:
            self.frightened_timer = max(0.0, self.frightened_timer - dt)

        # Update Player
        self._update_player(dt)

        # Update Ghosts
        if not self.cheat_ghost_freeze:
            self._update_ghosts(dt)

        # Check collisions & food
        self._check_item_consumption()
        self._check_ghost_collisions()

        # Check win condition (all pacgums eaten)
        if len(self.pacgums) == 0 and len(self.super_pacgums) == 0:
            self._advance_level()

    def _update_player(self, dt: float) -> None:
        base_speed = 4.0 if not self.cheat_speed_boost else 8.0
        step = base_speed * dt

        curr_ix = round(self.player_x)
        curr_iy = round(self.player_y)

        # Try changing to requested direction
        req_dir = self.player_next_dir
        if req_dir != Direction.NONE and req_dir != self.player_dir:
            if req_dir == Direction.OPPOSITES.get(self.player_dir):
                self.player_dir = req_dir
            elif (abs(self.player_x - curr_ix) < 0.2
                  and abs(self.player_y - curr_iy) < 0.2):
                if self.can_move(curr_ix, curr_iy, req_dir):
                    self.player_x = float(curr_ix)
                    self.player_y = float(curr_iy)
                    self.player_dir = req_dir

        if self.player_dir != Direction.NONE:
            dx, dy = self.player_dir
            next_x = self.player_x + dx * step
            next_y = self.player_y + dy * step

            check_ix = curr_ix
            check_iy = curr_iy
            if not self.can_move(check_ix, check_iy, self.player_dir):
                if dx > 0 and next_x > check_ix:
                    next_x = float(check_ix)
                elif dx < 0 and next_x < check_ix:
                    next_x = float(check_ix)
                elif dy > 0 and next_y > check_iy:
                    next_y = float(check_iy)
                elif dy < 0 and next_y < check_iy:
                    next_y = float(check_iy)

            self.player_x = max(0.0, min(float(self.grid_width - 1), next_x))
            self.player_y = max(0.0, min(float(self.grid_height - 1), next_y))

    def _update_ghosts(self, dt: float) -> None:
        speed = 2.8 if self.frightened_timer == 0 else 1.8
        step = speed * dt

        for ghost in self.ghosts:
            if ghost.is_eaten:
                ghost.respawn_timer -= dt
                if ghost.respawn_timer <= 0:
                    ghost.reset_to_start()
                continue

            gx = round(ghost.x)
            gy = round(ghost.y)

            # Pick valid direction at intersections
            stopped = ghost.dir == Direction.NONE
            centered = (abs(ghost.x - gx) < 0.15 and abs(ghost.y - gy) < 0.15)
            if stopped or centered:
                ghost.x = float(gx)
                ghost.y = float(gy)
                valid_dirs = []
                cardinals = [Direction.UP, Direction.RIGHT,
                             Direction.DOWN, Direction.LEFT]
                for d in cardinals:
                    if self.can_move(gx, gy, d):
                        opp = Direction.OPPOSITES.get(ghost.dir)
                        if d != opp or ghost.dir == Direction.NONE:
                            valid_dirs.append(d)

                if not valid_dirs:
                    for d in cardinals:
                        if self.can_move(gx, gy, d):
                            valid_dirs.append(d)

                if valid_dirs:
                    if self.frightened_timer > 0:
                        ghost.dir = random.choice(valid_dirs)
                    else:
                        px = self.player_x
                        py = self.player_y
                        valid_dirs.sort(
                            key=lambda d: ((gx + d[0] - px)**2
                                           + (gy + d[1] - py)**2)
                        )
                        ghost.dir = valid_dirs[0]

            if ghost.dir != Direction.NONE:
                ghost.x += ghost.dir[0] * step
                ghost.y += ghost.dir[1] * step

    def _check_item_consumption(self) -> None:
        px = round(self.player_x)
        py = round(self.player_y)

        if (px, py) in self.pacgums:
            self.pacgums.remove((px, py))
            self.score += self.config.points_per_pacgum

        if (px, py) in self.super_pacgums:
            self.super_pacgums.remove((px, py))
            self.score += self.config.points_per_super_pacgum
            self.frightened_timer = self.frightened_duration

    def _check_ghost_collisions(self) -> None:
        for ghost in self.ghosts:
            if ghost.is_eaten:
                continue

            dist = ((self.player_x - ghost.x)**2
                    + (self.player_y - ghost.y)**2)**0.5
            if dist < 0.6:
                if self.frightened_timer > 0:
                    ghost.is_eaten = True
                    ghost.respawn_timer = 7.0
                    self.score += self.config.points_per_ghost
                else:
                    if not self.cheat_invincible:
                        self._handle_player_death()
                        break

    def _handle_player_death(self) -> None:
        self.lives -= 1
        if self.lives <= 0:
            self.is_game_over = True
        else:
            self.player_x = float(self.player_spawn[0])
            self.player_y = float(self.player_spawn[1])
            self.player_dir = Direction.NONE
            self.player_next_dir = Direction.NONE
            for ghost in self.ghosts:
                ghost.reset_to_start()

    def _advance_level(self) -> None:
        if self.current_level_idx + 1 < len(self.mazes):
            self.load_level(self.current_level_idx + 1)
        else:
            self.is_victory = True

    # Cheat actions (Chapter VI.5)
    def toggle_invincibility(self) -> bool:
        self.cheat_invincible = not self.cheat_invincible
        return self.cheat_invincible

    def toggle_freeze_ghosts(self) -> bool:
        self.cheat_ghost_freeze = not self.cheat_ghost_freeze
        return self.cheat_ghost_freeze

    def toggle_speed(self) -> bool:
        self.cheat_speed_boost = not self.cheat_speed_boost
        return self.cheat_speed_boost

    def add_extra_life(self) -> int:
        self.lives += 1
        return self.lives

    def skip_level(self) -> None:
        self._advance_level()
