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