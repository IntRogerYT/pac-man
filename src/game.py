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
    """Ghost entity with arcade personality targeting and movement."""

    def __init__(self, ghost_id: int, start_x: int, start_y: int,
                 color: Tuple[int, int, int], corner_target: Tuple[int, int],
                 name: str) -> None:
        """Initialize a ghost with its spawn, color, and personality."""
        self.ghost_id = ghost_id
        self.name = name
        self.start_pos = (start_x, start_y)
        self.corner_target = corner_target
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
        """Initialize the engine and load the first level."""
        self.config = config
        self.mazes = mazes
        self.current_level_idx = 0

        self.score = 0
        self.lives = config.lives
        self.max_lives = 999

        self.cheat_invincible = False
        self.cheat_ghost_freeze = False
        self.cheat_speed_boost = False

        self.maze: List[List[int]] = []
        self.grid_width = 0
        self.grid_height = 0
        self.level_time_remaining = 0.0

        self.player_x = 0.0
        self.player_y = 0.0
        self.player_spawn = (0, 0)
        self.player_dir: Tuple[int, int] = Direction.NONE
        self.player_next_dir: Tuple[int, int] = Direction.NONE

        self.ghosts: List[Ghost] = []
        self.frightened_timer = 0.0
        self.frightened_duration = 7.0

        self.pacgums: Set[Tuple[int, int]] = set()
        self.super_pacgums: Set[Tuple[int, int]] = set()

        self.is_game_over = False
        self.is_victory = False
        self.level_completed = False
        self.game_over_reason = ""

        self.load_level(0)

    @property
    def current_level_config(self) -> LevelConfig:
        """Return the configuration for the current level."""
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

        cx = self.grid_width // 2
        cy = self.grid_height // 2

        if self.maze[cy][cx] == 15:
            best_c = (cx, cy)
            best_dist = 999999.0
            for y in range(self.grid_height):
                for x in range(self.grid_width):
                    if self.maze[y][x] != 15:
                        d = (x - cx)**2 + (y - cy)**2
                        if d < best_dist:
                            best_dist = d
                            best_c = (x, y)
            cx, cy = best_c

        self.player_spawn = (cx, cy)
        self.player_x = float(cx)
        self.player_y = float(cy)
        self.player_dir = Direction.NONE
        self.player_next_dir = Direction.NONE

        ghost_defs = [
            (0, 0, 0, (255, 0, 0), (self.grid_width - 1, 0), "Blinky"),
            (1, self.grid_width - 1, 0, (255, 184, 255),
             (0, 0), "Pinky"),
            (2, 0, self.grid_height - 1, (0, 255, 255),
             (self.grid_width - 1, self.grid_height - 1), "Inky"),
            (3, self.grid_width - 1, self.grid_height - 1,
             (255, 184, 82), (0, self.grid_height - 1), "Clyde"),
        ]
        self.ghosts = []
        for gid, gx, gy, col, corner_target, name in ghost_defs:
            self.ghosts.append(
                Ghost(gid, gx, gy, col, corner_target, name)
            )

        self.super_pacgums = {
            (0, 0),
            (self.grid_width - 1, 0),
            (0, self.grid_height - 1),
            (self.grid_width - 1, self.grid_height - 1),
        }

        target_count = lvl_cfg.pacgum
        all_corridor_cells = [
            (x, y) for y in range(self.grid_height)
            for x in range(self.grid_width)
            if self.maze[y][x] != 15
            and (x, y) not in self.super_pacgums
            and (x, y) != (cx, cy)
        ]
        if target_count <= 0 or target_count > len(all_corridor_cells):
            target_count = len(all_corridor_cells)

        random.seed(lvl_cfg.seed)
        chosen = random.sample(
            all_corridor_cells, min(target_count, len(all_corridor_cells))
        )
        self.pacgums = set(chosen)

    def can_move(self, x: int, y: int, direction: Tuple[int, int]) -> bool:
        """Check wall bitmask for movement from (x, y) in direction.

        Bits: 1=North wall, 2=East wall, 4=South wall, 8=West wall.
        Closed wall / pattern 42 cells (value 15) can never be traversed.
        """
        if not (0 <= x < self.grid_width and 0 <= y < self.grid_height):
            return False

        cell_val = self.maze[y][x]
        if cell_val == 15:
            return False

        dx, dy = direction
        nx = x + dx
        ny = y + dy
        if not (0 <= nx < self.grid_width and 0 <= ny < self.grid_height):
            return False
        if self.maze[ny][nx] == 15:
            return False

        if dx == 0 and dy == -1:
            return (cell_val & 1) == 0
        if dx == 1 and dy == 0:
            return (cell_val & 2) == 0
        if dx == 0 and dy == 1:
            return (cell_val & 4) == 0
        if dx == -1 and dy == 0:
            return (cell_val & 8) == 0

        return False

    def request_player_direction(self, direction: Tuple[int, int]) -> None:
        """Request a direction change for the player."""
        self.player_next_dir = direction

    def update(self, dt: float) -> None:
        """Advance game state by dt seconds."""
        if self.is_game_over or self.is_victory or self.level_completed:
            return

        self.level_time_remaining -= dt
        if self.level_time_remaining <= 0.0:
            self._handle_player_death("timeout")
            return

        if self.frightened_timer > 0.0:
            self.frightened_timer = max(0.0, self.frightened_timer - dt)

        self._update_player(dt)

        if not self.cheat_ghost_freeze:
            self._update_ghosts(dt)

        self._check_item_consumption()
        self._check_ghost_collisions()

        if len(self.pacgums) == 0 and len(self.super_pacgums) == 0:
            self._advance_level()

    def _update_player(self, dt: float) -> None:
        """Move the player, applying input, wall collisions, and speed."""
        base_speed = 4.2 if not self.cheat_speed_boost else 8.4
        step = base_speed * dt

        curr_ix = round(self.player_x)
        curr_iy = round(self.player_y)

        req_dir = self.player_next_dir
        if req_dir != Direction.NONE and req_dir != self.player_dir:
            if req_dir == Direction.OPPOSITES.get(self.player_dir):
                self.player_dir = req_dir
            else:
                dist_to_center = abs(self.player_x - curr_ix) + abs(
                    self.player_y - curr_iy
                )
                if dist_to_center < 0.35 and self.can_move(
                    curr_ix, curr_iy, req_dir
                ):
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

    def _get_ghost_target(self, ghost: Ghost) -> Tuple[float, float]:
        """Compute arcade target tile based on individual ghost personality.

        - Blinky: Chases player directly (Chapter VI.3).
        - Pinky: Ambushes 4 tiles ahead of player.
        - Inky: Unpredictable flanker using Blinky & player vectors.
        - Clyde: Chases player if >8 tiles away, otherwise scatters to corner.
        """
        px, py = self.player_x, self.player_y
        pdx, pdy = self.player_dir

        if ghost.ghost_id == 0:
            return px, py
        elif ghost.ghost_id == 1:
            return px + pdx * 4.0, py + pdy * 4.0
        elif ghost.ghost_id == 2:
            blinky = self.ghosts[0]
            lead_x = px + pdx * 2.0
            lead_y = py + pdy * 2.0
            return 2.0 * lead_x - blinky.x, 2.0 * lead_y - blinky.y
        else:
            dist_sq = (ghost.x - px)**2 + (ghost.y - py)**2
            if dist_sq >= 64.0:
                return px, py
            return float(ghost.corner_target[0]), float(ghost.corner_target[1])

    def _update_ghosts(self, dt: float) -> None:
        """Move ghosts using continuous arcade grid traversal."""
        speed = 3.2 if self.frightened_timer == 0 else 2.0
        step = speed * dt

        cardinals = [Direction.UP, Direction.LEFT,
                     Direction.DOWN, Direction.RIGHT]

        for ghost in self.ghosts:
            if ghost.is_eaten:
                ghost.respawn_timer -= dt
                if ghost.respawn_timer <= 0:
                    ghost.reset_to_start()
                continue

            curr_dir = ghost.dir
            if curr_dir == Direction.NONE:
                gx = round(ghost.x)
                gy = round(ghost.y)
                valid = [d for d in cardinals if self.can_move(gx, gy, d)]
                if valid:
                    ghost.dir = valid[0]
                    curr_dir = ghost.dir
                else:
                    continue

            dx, dy = curr_dir
            ghost.x += dx * step
            ghost.y += dy * step

            crossed = False
            tx, ty = round(ghost.x), round(ghost.y)

            if dx > 0 and ghost.x >= tx:
                crossed = (ghost.x - dx * step) < tx
            elif dx < 0 and ghost.x <= tx:
                crossed = (ghost.x - dx * step) > tx
            elif dy > 0 and ghost.y >= ty:
                crossed = (ghost.y - dy * step) < ty
            elif dy < 0 and ghost.y <= ty:
                crossed = (ghost.y - dy * step) > ty

            if crossed:
                ghost.x = float(tx)
                ghost.y = float(ty)

                opp = Direction.OPPOSITES.get(curr_dir, Direction.NONE)
                exits = [d for d in cardinals
                         if d != opp and self.can_move(tx, ty, d)]

                if not exits:
                    exits = [d for d in cardinals if self.can_move(tx, ty, d)]

                if not exits:
                    ghost.dir = Direction.NONE
                    continue

                if self.frightened_timer > 0.0:
                    ghost.dir = random.choice(exits)
                else:
                    tx_target, ty_target = self._get_ghost_target(ghost)
                    exits.sort(
                        key=lambda d: ((tx + d[0] - tx_target)**2
                                       + (ty + d[1] - ty_target)**2)
                    )
                    ghost.dir = exits[0]

    def _check_item_consumption(self) -> None:
        """Consume pacgums under the player and update score/effects."""
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
        """Handle player-ghost contact, eating ghosts or losing a life."""
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
                        self._handle_player_death("ghost")
                        break

    def _handle_player_death(self, reason: str) -> None:
        """Remove a life and respawn entities, or end the game."""
        self.lives -= 1
        if self.lives <= 0:
            self.is_game_over = True
            self.game_over_reason = reason
        else:
            self.player_x = float(self.player_spawn[0])
            self.player_y = float(self.player_spawn[1])
            self.player_dir = Direction.NONE
            self.player_next_dir = Direction.NONE
            self.level_time_remaining = float(
                self.current_level_config.level_max_time
            )
            for ghost in self.ghosts:
                ghost.reset_to_start()

    def _advance_level(self) -> None:
        """Load the next level or declare victory if none remain."""
        if self.current_level_idx + 1 < len(self.mazes):
            self.load_level(self.current_level_idx + 1)
        else:
            self.is_victory = True

    def toggle_invincibility(self) -> bool:
        """Toggle player invincibility and return the new state."""
        self.cheat_invincible = not self.cheat_invincible
        return self.cheat_invincible

    def toggle_freeze_ghosts(self) -> bool:
        """Toggle ghost freezing and return the new state."""
        self.cheat_ghost_freeze = not self.cheat_ghost_freeze
        return self.cheat_ghost_freeze

    def toggle_speed(self) -> bool:
        """Toggle the player speed boost and return the new state."""
        self.cheat_speed_boost = not self.cheat_speed_boost
        return self.cheat_speed_boost

    def reset_cheats(self) -> None:
        """Turn off all persistent cheat toggles."""
        self.cheat_invincible = False
        self.cheat_ghost_freeze = False
        self.cheat_speed_boost = False

    def add_extra_life(self) -> int:
        """Add one life up to the maximum and return the life count."""
        if self.lives + 1 <= self.max_lives:
            self.lives += 1
        else:
            print(f"Warning: Cannot add an extra life: already at the "
                  f"maximum of {self.max_lives} lives.")
        return self.lives

    def skip_level(self) -> None:
        """Cheat: Skip the current level immediately."""
        self._advance_level()

    def trigger_frightened(self) -> None:
        """Cheat: Trigger frightened ghost mode on demand."""
        self.frightened_timer = self.frightened_duration

    def add_score_bonus(self, points: int = 1000) -> int:
        """Cheat: Grant bonus score."""
        self.score += points
        return self.score
