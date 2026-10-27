try:
    import sys
    import json
    from pathlib import Path
    from pydantic import ValidationError

    from src.parser import Pacman_Parser
    from src.renderer import Renderer
except ModuleNotFoundError:
    print("Error: One or more required modules could not be imported. "
          "Run 'make install' before running the program.",
          file=sys.stderr)
    sys.exit(1)

try:
    from mazegenerator import MazeGenerator
except ModuleNotFoundError:
    print("Error: Missing module 'mazegenerator'. "
          "Run 'make install' to install it.", file=sys.stderr)
    sys.exit(1)


def strip_comments(content: str) -> str:
    """Remove lines starting with '#' as required by subject section V.2."""
    lines = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped.startswith("#"):
            lines.append(line)
    return "\n".join(lines)


def load_config(file_path_str: str) -> Pacman_Parser:
    """Load and validate the JSON configuration file."""
    path = Path(file_path_str)

    if path.suffix.lower() != ".json":
        sys.exit(f"Error: The configuration file must have a .json extension. "
                 f"Received: '{path.name}'")

    if not path.is_file():
        sys.exit(f"Error: Configuration file '{path}' not found.")

    try:
        raw_text = path.read_text(encoding="utf-8")
        clean_text = strip_comments(raw_text)

        try:
            data = json.loads(clean_text) if clean_text.strip() else {}
        except json.JSONDecodeError as err:
            print(f"Warning: Invalid JSON syntax in '{path}' ({err}). "
                  f"Falling back to default values.", file=sys.stderr)
            data = {}

        return Pacman_Parser.model_validate(data)

    except FileNotFoundError:
        sys.exit(f"Error: The configuration file '{path}' was not found.")
    except PermissionError:
        sys.exit(f"Error: Permission denied to read the file '{path}'.")
    except ValidationError as e:
        sys.exit(f"Error: Invalid configuration data in '{path}'.\n{e}")
    except UnicodeDecodeError:
        sys.exit(f"Error: Could not read '{path}': invalid UTF-8 sequence. "
                 f"The file must be UTF-8 encoded.")
    except Exception as e:
        sys.exit(f"Error: An unexpected error occurred: {e}")


def main() -> None:
    """Parse arguments, generate mazes, and start the renderer loop."""
    if len(sys.argv) != 2:
        sys.exit("Error: Invalid number of arguments.\nUsage: "
                 "python3 pac-man.py <config.json>")

    game = load_config(sys.argv[1])
    print("Configuration loaded successfully.")
    print(f"Highscore File: {game.highscore_filename} | Lives: {game.lives}\n")

    mazes = []
    for level in game.levels:
        print(f"=== Generating Level {level.level_id} ===")
        print(f"Dimensions: {level.width}x{level.height} | "
              f"Max Time: {level.level_max_time}s")

        try:
            maze_gen = MazeGenerator(
                size=(level.width, level.height),
                seed=level.seed,
                perfect=False
            )
            maze_gen.generate()
        except Exception as e:
            sys.exit(f"Error: Maze generation failed for level "
                     f"{level.level_id} ({level.width}x{level.height}, "
                     f"seed={level.seed}): {e}")

        mazes.append(maze_gen.maze)
    try:
        renderer = Renderer(game, mazes)
        renderer.run()
    except KeyboardInterrupt:
        print("\nExiting program...")


if __name__ == "__main__":
    main()
