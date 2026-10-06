# Team Organization

## Team Members
* **lfleitas**: Backend Logic and Core Algorithms (JSON parsing, maze generation integration, game logic).
* **rcamps-v (Roger)**: Visuals, Menus, and Graphical Interface.

## Work Distribution
The project is split into two independent but interconnected modules to allow parallel development:
1. **Engine & Logic**: Focuses on parsing the `config.json` securely using Pydantic, handling the `mazegenerator` library, and processing backend game rules.
2. **Graphics & UI**: Focuses on rendering the maze, displaying menus, handling user inputs, and managing the game loop visuals.

## Coordination & Decision Making
* **Task Management**: We use GitHub Projects (Kanban Board) to track features, bugs, and tasks (To Do, In Progress, Done).
* **Code Integration**: All code changes are submitted via Pull Requests (PRs). The other team member must review and approve the PR before merging into the `main` branch to ensure quality and prevent silent conflicts.
* **Communication**: Daily syncs to discuss blockers, validate progress, and agree on data structures (e.g., how the backend will pass the maze matrix to the frontend).