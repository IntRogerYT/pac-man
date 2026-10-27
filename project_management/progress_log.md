# Progress Log

## October 5, 2026 (Monday)
### Project Kickoff
- Reviewed project subject and mandatory requirements.
- Defined overall architecture separating Backend Logic and Frontend UI modules.
- Assigned responsibilities between team members.
- Created repository structure and initialized Git workflow.
- Set up project management board (Kanban).

---

## October 6, 2026 (Tuesday)
### Environment Setup & Planning
- Created virtual environment and dependency management workflow.
- Installed and evaluated required libraries (Pydantic and assigned A-Maze-ing package).
- Defined initial JSON configuration structure.
- Started drafting project management documentation.
- First commit pushed; local status of the project start added.
- Merged PR #1 (`feature/config-pydantic`) and committed the initial project management status.

---

## October 7, 2026 (Wednesday)
### Configuration System Development
- Implemented configuration loader with support for JSON validation.
- Added Pydantic models for configuration parsing.
- Implemented safe default values for invalid or missing fields.
- Completed testing of configuration parsing.
- Acceptance tests BE-01, BE-02, and BE-03 passed.
- Refactored the parser and added strict error clamping.
- Removed the obsolete `data` directory.

---

## October 8, 2026 (Thursday)
### Maze Generator Integration
- Integrated assigned A-Maze-ing package.
- Added support for per-level seed handling.
- Implemented fallback random seed generation when seed is omitted.
- Added exception handling around maze generation process.
- Acceptance tests BE-05 and BE-06 passed.
- Improved parser and seed handling.
- Added `.gitignore` for cache directories and included `pygame` in `requirements.txt`.
- Added the `Renderer` class and the font asset used for game display.
- Merged PRs #4 (project management), #6 and #7 (renderer), and #8 (parser).

---

## October 9, 2026 (Friday)
### Backend Stabilization
- Refactored configuration models to simplify level definitions.
- Fixed validation issues discovered during testing.
- Added logging messages for invalid configuration parameters.
- Performed internal review of backend design.

---

## October 12, 2026 (Monday)
### Frontend Proof of Concept
- Implemented initial rendering engine prototype.
- Created main menu structure.
- Added maze visualization using test matrices from backend.
- Connected frontend rendering loop with backend output.
- Acceptance tests BE-04, FE-01, FE-02, FE-03, IN-01, IN-02, and IN-03 passed.
- Removed `.venv` from version tracking and updated `.gitignore`.
- Completed the README with subject requirements and architecture.
- Excluded the "42" pattern from pellets and implemented arcade-style ghost movement.
- Completed cheat mode with HUD indicators, hotkeys, and documentation.

---

## October 13, 2026 (Tuesday)
### Gameplay Foundations
- Implemented player movement system.
- Added collision detection against maze walls.
- Created basic game loop and scene management structure.
- Established communication interfaces between backend and frontend modules.
- Added animations for Pac-Man and super pac-gums.
- Merged PRs #10 (README and packaging), #11 (maze 42 and ghost movement fixes), and #12 (cheat mode feature).

---

## October 14, 2026 (Wednesday)
### Ghost System Development
- Implemented ghost entity classes.
- Added autonomous movement behavior.
- Tested navigation through generated maze corridors.
- Began implementation of player-ghost interactions.
- Handled `KeyboardInterrupt` during renderer execution (PR #16).
- Added in-game instructions explaining cheat mode commands, plus a reset option (PR #18).
- Improved game over handling with specific reasons for player death (PR #19).
- Changed the minimum time value from 1 to 42 and fixed the README (PR #20).
- Added a build script to create the executable, with the corresponding Makefile variable.

---

## October 15, 2026 (Thursday)
### Pacgum & Scoring System
- Implemented pacgum placement logic.
- Added score tracking system.
- Implemented collection mechanics for regular pacgums.
- Linked gameplay events with score updates.

---

## October 16, 2026 (Friday)
### Advanced Gameplay Features
- Implemented super-pacgum behavior.
- Added temporary ghost state changes after power pellet collection.
- Continued balancing movement and collision systems.
- Started work on level progression mechanics.

---

## October 19, 2026 (Monday)
### Highscore Management
- Implemented persistent highscore storage.
- Added loading and saving of scores.
- Created validation rules for player name inputs.
- Limited stored highscores to the top ten entries.
- Added dependency versioning to `requirements.txt`.
- Added `max_value` validation in the parser and the add-lives logic in the game, and hid the pygame welcome message (PR #24).
- Merged the packaging branch (PR #22).

---

## October 20, 2026 (Tuesday)
### User Interface Improvements
- Added HUD displaying score, lives, level, and timer.
- Improved menu navigation.
- Added instructions screen layout.
- Started implementation of game over and victory screens.

---

## October 21, 2026 (Wednesday)
### Game State Management
- Implemented pause menu functionality.
- Added victory and defeat state transitions.
- Improved scene switching and resource management.
- Conducted integration testing between gameplay systems.
- Added a unit test suite in `tests/` (119 tests) covering the parser, highscores, game engine, renderer, main entry point, and maze generator.
- Added a `test` rule to the Makefile (`unittest discover`).
- Applied lint adjustments in `src/` and reorganized imports in `renderer.py`.
- Verified `make test`, `make lint`, and `make lint-strict` all pass (PR #28).

---

## October 22, 2026 (Thursday)
### Cheat Mode & Review Tools
- Implemented evaluation support features.
- Added debugging utilities and testing shortcuts.
- Reviewed project compliance against mandatory subject requirements.
- Performed regression testing after feature integration.
- Added docstrings to every function, class, and method and removed inline comments (PR #29).
- Rewrote the README to meet the 42 subject requirements (PR #30).

---

## October 23, 2026 (Friday)
### Bug Fixing & Optimization
- Resolved issues identified during integration testing.
- Improved exception handling and error reporting.
- Optimized rendering loop performance.
- Validated stable framerate during extended play sessions.

---

## October 26, 2026 (Monday)
### Final Documentation & Validation
- Updated acceptance test documentation.
- Completed project management documents:
  - Project Analysis
  - Team Organization
  - Risk Analysis
  - Progress Log
- Verified completed milestones against project timeline.
- Performed final project review and readiness assessment before packaging and final polishing phase.
- Adjusted renderer functions for MLX compliance and reworked `renderer.py` (PR #31).
- Fixed import errors in `pac-man.py` (PR #32).
- Changed the parser to store the `highscore.txt` contents in a dictionary (PR #34).
- Improved warning messages.
- Made installation mandatory in the package command and edited the script to support it.
- Removed the unused `maze.py`.
- Merged PR #35.

---

## October 27, 2026 (Tuesday)
### Final Fixes & Merges
- Sorted levels before clamping in the parser (PR #36).
- Removed the testing code from production.
- Fixed flake8 issues in the parser (PRs #39, #40, #41).
- Refactored the level id sorting function.
- Improved error messages and warnings.
- Resolved merge conflicts and merged `Fixes_&_bugs` into `main` (PRs #42, #43).