# Acceptance Test Plan

## Overview
This document tracks the validation of core features and the resolution of bugs discovered during development. Tests are divided into Backend Logic, Frontend Visuals, and Integration.

## Feature Testing Matrix

### 1. Backend & Configuration (Assigned to: lfleitas)

| Test ID | Feature | Expected Behavior | Status | Tested By | Date |
|:---:|---|---|:---:|:---:|:---:|
| BE-01 | Config Parsing | `config.json` is successfully loaded and validated by Pydantic. | Passed | lfleitas | Oct 7 |
| BE-02 | Invalid Config | Program gracefully fails and logs clear errors when `config.json` is malformed or missing keys. | Passed | lfleitas | Oct 7 |
| BE-03 | Maze Generation | `MazeGenerator` successfully instantiates using parameters from the config file. | Passed | lfleitas | Oct 7 |
| BE-04 | Matrix Output | The generated maze translates into a readable matrix/array format for the frontend. | Pending | | |
| BE-05 | Level Seed Fallback | If a level omits `seed`, the parser assigns a randomized integer seed via `random.randint`. | Passed | lfleitas | Oct 8 |
| BE-06 | Maze Generator Safety | `MazeGenerator` runs with `perfect=False` and handles library exceptions cleanly without tracebacks. | Passed | lfleitas | Oct 8 |

### 2. Frontend & UI (Assigned to: rcamps-v)
| Test ID | Feature | Expected Behavior | Status | Tested By | Date |
|:---:|---|---|:---:|:---:|:---:|
| FE-01 | Main Menu | The main menu renders correctly and responds to user inputs. | ⬜ Pending | | |
| FE-02 | Maze Rendering | The visual engine accurately draws walls, paths, and entities based on a dummy matrix. | ⬜ Pending | | |
| FE-03 | Frame Rate | The graphical loop maintains a stable framerate without memory leaks. | ⬜ Pending | | |

### 3. Integration & Gameplay (Assigned to: Team)
| Test ID | Feature | Expected Behavior | Status | Tested By | Date |
|:---:|---|---|:---:|:---:|:---:|
| IN-01 | Handshake | Backend passes the generated maze matrix to the frontend without data loss. | ⬜ Pending | | |
| IN-02 | Movement Collision | Player character cannot pass through maze walls defined by the backend logic. | ⬜ Pending | | |
| IN-03 | Win/Loss States | Game accurately detects and triggers end screens based on backend rules (e.g., lives == 0). | ⬜ Pending | | |

---

## Bug Tracking Log

*Use this section to log any unexpected behaviors found during testing or regular development.*

| Bug ID | Related Feature | Description | Priority | Status | Fix / Notes |
|:---:|---|---|:---:|:---:|---|
| BUG-001 | BE-01 | `ValidationError` crashed the program when `level` array dimensions didn't match the model. | High | Fixed | Redesigned model to use `LevelConfig` objects instead of 3D arrays. |
| BUG-002 | BE-02 | Invalid config inputs threw Python tracebacks, violating project subject rules. | High | Fixed | Implemented `model_validator(mode='before')` to clamp faulty data to safe defaults and suppress tracebacks. |
| BUG-003 | BE-03 | Levels reused a single static global seed, preventing procedural randomness in subsequent stages. | Medium | Fixed | Moved `seed` property into `LevelConfig`, removing root seed and generating random seeds when absent. |
