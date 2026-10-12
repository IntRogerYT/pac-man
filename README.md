*This project has been created as part of the 42 curriculum by rcamps-v, lfleitas.*

# Pac-Man (Ghosts! More ghosts!)

## Description
A modern Python implementation of the classic arcade game **Pac-Man**, featuring procedural maze generation via external libraries, custom configuration parsing with fallback handling, a persistent highscore management system, and retro audio-visual rendering using Pygame.

## Instructions

### Requirements
- Python 3.10+
- Virtual environment (`venv`) and package dependencies listed in `requirements.txt`.

### Installation
Install project dependencies and build the local wheel packages:
```bash
make install
```

### Running the Game
To run the game, provide a configuration JSON file as the single argument:
```bash
make run
# or directly:
python3 pac-man.py config.json
```

### Debugging
Run the game using Python's built-in debugger (`pdb`):
```bash
make debug
```

### Linting & Code Standards
Adhere to the `flake8` coding standard and static type checking with `mypy`:
```bash
make lint
make lint-strict
```

### Cleanup
Remove cached bytecode, build artifacts, and temporary test files:
```bash
make clean
```

---

## Configuration
The game is configured through a JSON file (e.g. `config.json`).
Lines starting with `#` are treated as comments and ignored during parsing.

Supported keys and default fallback values:
- `highscore_filename`: Name of the highscores storage file (default: `"scores.txt"`).
- `lives`: Number of starting lives (default: `3`, clamped $\ge 1$).
- `points_per_pacgum`: Points awarded per regular pacgum eaten (default: `10`).
- `points_per_super_pacgum`: Points awarded per super-pacgum eaten (default: `50`).
- `points_per_ghost`: Points awarded per ghost consumed (default: `200`).
  - *Enforced hierarchy*: Points per Ghost > Super-Pacgum > Pacgum.
- `levels`: Array containing configurations for at least 10 levels. If fewer than 10 levels are defined in the file, missing levels are automatically generated using safe defaults.
  - `level_id`: Sequential integer level identifier ($1, 2, \dots, N$).
  - `width` / `height`: Grid dimensions for the level maze (default: $15 \times 15$, minimum: $5 \times 5$).
  - `level_max_time`: Maximum time in seconds allocated to finish the level (default: `142`).
  - `pacgum`: Number of pacgums distributed throughout the maze corridors.
  - `seed`: Level-specific seed for procedural generation. If missing or invalid, a secure random seed is generated on the fly.

Unknown keys in the configuration file are safely ignored (`extra='ignore'`), and invalid values are clamped with informative warnings to prevent application crashes without Python tracebacks.

---

## Highscore System
The highscore module (`src/highscore.py`) maintains persistent top 10 records across gameplay sessions:
- Records player names and integer scores.
- Restricts player names to a maximum of 10 characters consisting strictly of alphanumeric characters and spaces.
- Robust file handling guarantees that missing, unformatted, or corrupted highscore files are handled gracefully without raising exceptions or interrupting gameplay.
- Top scores are displayed on the Highscores screen accessible from the Main Menu, and updated upon completing a game session (Game Over or Victory).

---

## Maze Generation
Mazes are generated procedurally using the external `mazegenerator` package (`mazegenerator-2.1.0-py3-none-any.whl`):
- Generation is initialized with `perfect=False` to produce non-perfect mazes with multiple corridors and loops appropriate for Pac-Man navigation.
- Each level utilizes its own seed to allow deterministic replayability when specified, or variety when randomized.
- Generator calls are wrapped with robust exception handling to protect the game loop against external library failures.

---

## General Software Architecture
The application follows a modular, object-oriented design:
- **`pac-man.py`**: Main application entrypoint; validates CLI parameters, loads the configuration, generates all level mazes, and launches the game loop.
- **`src/parser.py`**: Pydantic models (`Pacman_Parser`, `LevelConfig`) handling JSON deserialization, comment stripping, boundary clamping, and default fallbacks.
- **`src/game.py`**: Core domain logic (`GameEngine`, `Ghost`, `Direction`). Manages player movement, ghost AI (chase, scatter, edible, and respawn behaviors), pellet consumption, wall collisions, timers, and evaluation cheats.
- **`src/highscore.py`**: `HighscoreManager` responsible for reading, sanitizing, sorting, and persisting highscore data.
- **`src/renderer.py`**: Pygame graphical interface (`Renderer`). Controls window presentation, menu state transitions (Menu, Highscores, Instructions, Game, Pause, Game Over, Victory), and HUD rendering.

---

## Controls & Evaluation Cheats
- **Movement**: Arrow Keys or `W`, `A`, `S`, `D`.
- **Pause / Resume**: `P` or `ESC`.
- **Cheats (Chapter VI.5)**:
  - `1`: Toggle Invincibility (no lives lost from ghosts).
  - `2`: Freeze / Unfreeze ghost movement.
  - `3`: Add extra life (+1).
  - `4`: Toggle speed boost.
  - `5`: Skip to next level.
  - `6`: Trigger frightened / edible ghost mode.
  - `7`: Add bonus score (+1000 points).

---

## Resources & AI Usage
- **Documentation & References**:
  - Pygame Community Documentation: https://www.pygame.org/docs/
  - Pydantic Documentation: https://docs.pydantic.dev/
  - Pac-Man Dossier (Game mechanics & Ghost AI design): https://pacman.holycow.com/
- **AI Tooling**:
  - Google Antigravity / Gemini was used for code architecture planning, docstring drafting, Pydantic validator design, and automated test matrix tracking.

---

## Project Management
Full project management tracking, risk analysis, acceptance tests, and progress logs are maintained in the dedicated [`project_management/`](file:///home/lfleitas/M4/Pac-Man/pac-man/project_management) directory:
- [`project_management/project_analysis.md`](file:///home/lfleitas/M4/Pac-Man/pac-man/project_management/project_analysis.md)
- [`project_management/team_organization.md`](file:///home/lfleitas/M4/Pac-Man/pac-man/project_management/team_organization.md)
- [`project_management/risk_analysis.md`](file:///home/lfleitas/M4/Pac-Man/pac-man/project_management/risk_analysis.md)
- [`project_management/acceptance_tests.md`](file:///home/lfleitas/M4/Pac-Man/pac-man/project_management/acceptance_tests.md)
- [`project_management/progress_log.md`](file:///home/lfleitas/M4/Pac-Man/pac-man/project_management/progress_log.md)