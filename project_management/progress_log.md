# Actual Progress Tracking

## Day 0: October 5, 2026
* **Tasks completed**:
  * Initialized Git repository and defined the project structure.
  * Configured the `Makefile` with rules for environment creation, dependency installation, running, and strict linting.
  * Implemented backend `config.json` validation using Python's `Pydantic` library.
  * Evaluated package managers (`pip` vs. `uv`) and strictly adopted `pip` to ensure compatibility with 42 evaluation constraints.
* **Blockers**: Path resolution issues with local `.whl` dependencies, resolved by creating a dedicated `libs/` directory.

## Day 1: October 6, 2026
* **Tasks completed**:
  * Kickoff meeting to define roles and responsibilities.
  * Validated Day 0 environment setup and architecture choices as a team.
  * Delegated core domains: lfleitas (Algorithms/Backend) and rcamps-v (Visuals/Menus).
  * Established the GitHub Kanban board to track upcoming features and established the Pull Request review workflow.
* **Blockers**: None. Clear roadmap established.

## Day 2: October 7, 2026
* **Tasks completed**:
  * Resolved a dimensionality mismatch between the `config.json` arrays and the Pydantic parser.
  * Redesigned the level architecture: shifted from pre-calculated matrices to procedural generation parameters (width, height, max time) to fully utilize the `mazegenerator` library.
  * Implemented core game logic constraints in the parser: Points hierarchy (Ghost > Super Pacgum > Pacgum) and Pacgum spatial limits based on maze area.
  * Refactored validation to comply with Subject Chapter V.3: The parser now ignores unknown keys (`extra='ignore'`), enforces a minimum of 10 levels, and safely clamps missing or invalid values to defaults with console warnings instead of throwing Python tracebacks.
  * Updated `main.py` to iterate through the validated `LevelConfig` objects and generate distinct mazes dynamically.
* **Decisions & Blockers**:
  * Decided to maintain a linear `List` structure for levels instead of a dictionary to simplify the sequential game loop.
  * Deferred the definition of absolute maximum graphical bounds (e.g., maximum supported maze size) to a dedicated GitHub Issue for later team discussion.

## Day 3: October 8, 2026
* **Tasks completed**:
  * Refactored seed architecture: Migrated from a single global seed to independent, level-scoped seeds (`seed` field inside `LevelConfig`).
  * Implemented procedural fallback for level seeds: When `seed` is omitted or invalid in `config.json`, the parser automatically generates an integer seed using `random.randint(...)` to ensure level variability without throwing exceptions.
  * Cleaned up the global `Pacman_Parser` model by removing the deprecated root `seed` attribute while letting `extra='ignore'` safely bypass legacy root seeds.
  * Updated `MazeGenerator` integration in `pac-man.py` with `perfect=False` and cleanly encapsulated generation calls inside `try...except` blocks to handle external library failures gracefully without tracebacks.
* **Decisions & Blockers**:
  * **Decision**: Enforced that each level owns its generation seed directly, facilitating debugging/replayability for specific stages while guaranteeing distinct mazes across levels by default.
  * **Blockers**: None. Config parsing and procedural generation requirements fully aligned with Subject Chapters V.1, V.3, and V.4.

## Day 4: October 12, 2026
* **Tasks completed**:
  * Implemented backend board matrix and entity distribution in [`src/game.py`](file:///home/lfleitas/M4/Pac-Man/pac-man/src/game.py) (`BE-04`): Pac-Man in the center, 4 ghosts in 4 corners, 4 super-pacgums in corners, and pacgums across maze corridors.
  * Created persistent highscore system in [`src/highscore.py`](file:///home/lfleitas/M4/Pac-Man/pac-man/src/highscore.py) complying with Chapter V.5: Top 10 scores, robust error fallback, and name sanitization (max 10 alphanumeric and space characters).
  * Implemented full game state loop, entity collisions, ghost edible mode, timers, and level progression logic.
  * Added evaluation cheat modes (Chapter VI.5): invincibility (1), ghost freeze (2), extra life (3), speed boost (4), and level skip (5).
  * Upgraded [`src/renderer.py`](file:///home/lfleitas/M4/Pac-Man/pac-man/src/renderer.py) with Main Menu (Start, Highscores, Instructions, Exit), real-time HUD (Score, Lives, Level, Time), Pause Menu, and Game Over / Victory name entry screen.
  * Validated full code compliance with `flake8` and `mypy` without any errors (`make lint`).
* **Decisions & Blockers**:
  * **Decision**: Connected all procedural levels directly into the GameEngine to support full 10+ level sequential progression.
  * **Blockers**: None. All core integration milestones passed.