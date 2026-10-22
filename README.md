*This project has been created as part of the 42 curriculum by rcamps-v, lfleitas.*

# Pac-Man (Ghosts! More ghosts!)

## Description

Pac-Man is a modern Python implementation of the classic arcade game. The
project recreates the core Pac-Man experience with procedurally generated
mazes, four ghosts with distinct behaviours, persistent highscores, and a
complete graphical interface built with Pygame.

The goal of the project is to practise modular software design while combining
several technical areas: JSON configuration validation with Pydantic, external
maze-generation libraries, game-state management, simple artificial
intelligence for ghosts, collision detection, timers, persistent storage, and
real-time rendering.

The player moves through a maze collecting pacgums. Eating all regular and
super-pacgums completes the level. Super-pacgums temporarily make ghosts edible.
The game ends when the player runs out of lives or when all configured levels
have been completed.

## Instructions

### Requirements

- Python 3.10 or newer.
- `make`.
- `python3-venv` support.
- A graphical environment capable of opening a Pygame window.

All Python dependencies are declared in `requirements.txt`:

- `pygame` for the graphical interface and input handling.
- `pydantic` for configuration validation.
- `flake8` and `mypy` for linting and static type checking.
- The local `mazegenerator` wheel located in `libs/`.

### Installation

Create the virtual environment and install all dependencies:

```bash
make install
```

No compilation step is required because the game runs directly from Python
source. An optional standalone package can be built with PyInstaller:

```bash
make package
```

This creates a distributable archive under `dist/`.

### Running the Game

Run the game through the Makefile:

```bash
make run
```

Or run it directly with a configuration file:

```bash
python3 pac-man.py config.json
```

The configuration file must exist and must use the `.json` extension. The
provided `config.json` is a working example.

### Debugging

Run the game with Python's built-in debugger:

```bash
make debug
```

### Testing

Run the unit test suite:

```bash
make test
```

The tests cover configuration parsing, game logic, ghost behaviour, highscores,
rendering helpers and the main entrypoint.

### Linting and Type Checking

Check the code with `flake8` and `mypy`:

```bash
make lint
make lint-strict
```

`make lint-strict` runs `mypy --strict`.

### Cleanup

Remove caches, generated files and the virtual environment:

```bash
make clean
```

## Configuration

The game is configured through a JSON file passed as the only command-line
argument. Lines whose first non-whitespace character is `#` are treated as
comments and removed before parsing.

Unknown keys are ignored. Invalid or out-of-range values are clamped to safe
defaults and reported with warnings instead of crashing the program.

### Global settings

| Key | Description | Default | Accepted range |
|---|---|---:|---|
| `highscore_filename` | File used to store highscores | `"scores.txt"` | Valid filename with an extension |
| `lives` | Starting number of lives | `3` | 1 to 999 |
| `points_per_pacgum` | Points for a regular pacgum | `10` | 0 to 1000 |
| `points_per_super_pacgum` | Points for a super-pacgum | `50` | 0 to 10000 |
| `points_per_ghost` | Points for eating an edible ghost | `200` | 0 to 100000 |

The points hierarchy is enforced: `points_per_ghost` must be greater than
`points_per_super_pacgum`, which must be greater than `points_per_pacgum`.
If the hierarchy is invalid, the defaults `200 > 50 > 10` are restored.

### Level settings

`levels` must be an array. The project requires at least 10 levels; if fewer are
provided, the missing levels are generated automatically with default values.

| Key | Description | Default | Accepted range |
|---|---|---:|---|
| `level_id` | Sequential level identifier | `1` | 1 to 100 |
| `width` | Maze width in cells | `15` | 5 to 42 |
| `height` | Maze height in cells | `15` | 5 to 42 |
| `level_max_time` | Time limit in seconds | `142` | 42 to 999 |
| `pacgum` | Requested number of pacgums | `0` | 0 to `width * height - 5` |
| `seed` | Maze generation seed | random | Any integer |

Level identifiers are forced to be sequential (`1, 2, ..., N`). If `pacgum` is
`0`, or larger than the number of available corridor cells, the engine places
pacgums in every available corridor cell. If `seed` is missing or invalid, a
random seed is generated.

### Example

```json
{
  "highscore_filename": "scores.txt",
  "lives": 3,
  "points_per_pacgum": 10,
  "points_per_super_pacgum": 50,
  "points_per_ghost": 200,
  "levels": [
    {
      "level_id": 1,
      "width": 15,
      "height": 15,
      "level_max_time": 120,
      "pacgum": 100,
      "seed": 42
    }
  ]
}
```

## Highscore System

Highscores are managed by `HighscoreManager` in `src/highscore.py` and stored in
the file named by `highscore_filename`.

The system works as follows:

- Scores are stored as a JSON list of objects with `name` and `score` fields.
- Only the top 10 scores are kept, sorted in descending order.
- Names are sanitised: only letters, digits and spaces are allowed, the result
  is uppercased and limited to 10 characters. An empty name becomes `PLAYER`.
- Scores are converted to non-negative integers.
- A missing, empty, malformed or unreadable file is handled gracefully: the
  manager falls back to an empty score list without interrupting the game.
- Scores are saved when the player finishes a game, either by game over or
  victory, after entering a name on the endgame screen.

This format was chosen because it is human-readable, easy to inspect and does
not require an external database. The defensive loading logic keeps the game
playable even if the highscore file is corrupted or manually edited.

## Maze Generation

Mazes are generated with the assigned A-Maze-ing maze generator, distributed
here as the external `mazegenerator` package provided in
`libs/mazegenerator-2.1.0-py3-none-any.whl` and installed from
`requirements.txt`.

For each level, `pac-man.py` creates a generator with the level parameters:

```python
maze_gen = MazeGenerator(
    size=(level.width, level.height),
    seed=level.seed,
    perfect=False,
)
maze_gen.generate()
```

The resulting matrix is stored in `maze_gen.maze` and passed to the game engine.
Using `perfect=False` produces mazes with loops and multiple paths, which are
more suitable for Pac-Man than a perfect maze with a single solution. Each level
uses its own seed, so a configured seed makes the level reproducible while a
random seed provides variation.

Generation is wrapped in error handling so that failures from the external
library produce a clear application error instead of an unhandled traceback.

Maze cells use a wall bitmask: `1` = north wall, `2` = east wall, `4` = south
wall and `8` = west wall. Cells with value `15` are treated as closed cells
(pattern 42) and can never be traversed or contain pacgums.

## Implementation

The game uses a modular architecture built around a central game engine and a
separate renderer.

- **Configuration**: `pac-man.py` reads the JSON file, strips comment lines and
  validates the data with Pydantic models. Validators clamp invalid values and
  generate missing levels or seeds before the game starts.
- **Game engine**: `GameEngine` owns the current level, score, lives, timers,
  player position, ghosts and collectible sets. It exposes an `update(dt)`
  method that advances the simulation independently of the renderer.
- **Movement and collisions**: movement is continuous rather than tile-by-tile.
  The engine uses the maze wall bitmask to prevent crossing walls and snaps the
  player to tile centres when turning corners. Ghosts follow the same grid
  constraints and avoid reversing direction unless they reach a dead end.
- **Ghost AI**: each ghost has a different targeting strategy. Blinky chases the
  player directly, Pinky targets a point four tiles ahead, Inky uses a vector
  based on Blinky and the player, and Clyde chases from a distance but retreats
  towards its corner when close. During frightened mode, ghosts choose random
  valid exits and can be eaten.
- **Game rules**: eating all pacgums and super-pacgums advances the level. The
  level timer causes a life loss when it reaches zero. Ghost contact also costs
  a life unless invincibility is active. The game tracks game over and victory
  states.
- **Rendering**: `Renderer` runs the Pygame loop at approximately 30 FPS. It
  draws the maze, pacgums, super-pacgums, animated Pac-Man and ghosts, plus the
  HUD showing score, lives, level and remaining time. It also manages the main
  menu, highscores screen, instructions screen, pause menu and endgame screen.
- **Evaluation cheats**: invincibility, ghost freeze, extra life, speed boost,
  level skip, frightened mode and bonus score are available through the cheat
  menu.

## General Software Architecture

The application is organised into a small number of modules with clear
responsibilities:

```text
pac-man.py
    |
    +-- src.parser.Pacman_Parser / LevelConfig
    |       Configuration models, defaults and validation
    |
    +-- mazegenerator.MazeGenerator
    |       Procedural maze matrix generation
    |
    +-- src.renderer.Renderer
            |
            +-- src.game.GameEngine
            |       Game state, movement, collisions, ghost AI, progression
            |       Uses Direction and Ghost
            |
            +-- src.highscore.HighscoreManager
                    Persistent top-10 score storage
```

- **`pac-man.py`**: entrypoint. Validates command-line arguments, loads the
  configuration, generates one maze per level and launches the renderer.
- **`src/parser.py`**: Pydantic models `LevelConfig` and `Pacman_Parser`, plus
  validators for clamping, defaults, level sequencing and seed generation.
- **`src/game.py`**: domain layer. Contains `Direction`, `Ghost` and
  `GameEngine`, including player movement, ghost targeting, collisions, timers,
  level progression and cheat actions.
- **`src/highscore.py`**: `HighscoreManager`, responsible for loading,
  sanitising, sorting, trimming and saving scores.
- **`src/renderer.py`**: presentation layer. `Renderer` owns a `GameEngine` and
  a `HighscoreManager`, handles Pygame events and draws every screen.
- **`src/maze.py`**: small standalone example of generating and printing a maze
  with the external library.

Data flows in one direction: configuration and generated mazes enter the
renderer, the renderer drives the engine, and the engine state is read back for
drawing. The engine has no Pygame dependency, which keeps gameplay logic
independent from the graphical layer.

## Controls and Evaluation Cheats

- **Movement**: arrow keys or `W`, `A`, `S`, `D`.
- **Pause / resume**: `P` or `ESC`.
- **Cheat mode**: `C` toggles cheat mode. Cheats `1` to `7` only work while
  cheat mode is enabled; disabling it also resets active cheats.
- **`1`**: toggle invincibility.
- **`2`**: freeze or unfreeze ghosts.
- **`3`**: add an extra life.
- **`4`**: toggle the speed boost.
- **`5`**: skip to the next level.
- **`6`**: trigger frightened (edible ghost) mode.
- **`7`**: add 1000 bonus points.

## Resources

- [Pygame documentation](https://www.pygame.org/docs/) — rendering, events,
  fonts and timing.
- [Pydantic documentation](https://docs.pydantic.dev/) — models and validators.
- [The Pac-Man Dossier](https://pacman.holycow.com/) — arcade game mechanics,
  ghost personalities and targeting behaviour.
- [Python documentation](https://docs.python.org/3/) — standard library,
  `unittest`, `json` and `pathlib`.

### AI usage

AI tools (Google Antigravity / Gemini) were used as development assistants for
specific tasks, not as a replacement for implementation or verification:

| Task | Project part |
|---|---|
| Architecture planning and module organisation | Overall project structure, `src/` modules |
| Pydantic validator design and fallback behaviour | `src/parser.py` |
| Docstring drafting and review | `src/` and `pac-man.py` |
| Test matrix and acceptance-test tracking | `project_management/acceptance_tests.md` |
| Documentation drafting and review | `README.md`, project-management documents |

All AI-assisted output was reviewed, integrated and tested by the team. The game
logic, configuration handling and rendering were validated with the unit test
suite and the linting commands described above.

## Project Management

The project followed an Agile-inspired Kanban workflow using GitHub Projects.
Work was divided between two roles: lfleitas focused on backend logic and core
algorithms, while rcamps-v focused on visuals, menus and the graphical
interface. Features were tracked on the Kanban board, developed in small
branches and integrated through pull requests reviewed by the other team member.

The project was organised in five phases: setup and architecture, core
development, integration, optimisation, and polish and testing. Risks such as
integration conflicts, rendering complexity and schedule overruns were tracked
together with mitigation strategies.

The dedicated project-management directory contains the analysis, team
organisation, risk analysis, acceptance tests and progress log:
[`project_management/`](project_management/).

- [`project_management/project_analysis.md`](project_management/project_analysis.md)
- [`project_management/team_organization.md`](project_management/team_organization.md)
- [`project_management/risk_analysis.md`](project_management/risk_analysis.md)
- [`project_management/acceptance_tests.md`](project_management/acceptance_tests.md)
- [`project_management/progress_log.md`](project_management/progress_log.md)
