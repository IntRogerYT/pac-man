try:
    import sys
    import json
    from pathlib import Path
    from pydantic import ValidationError

    from src.parser import Pacman_Parser
    from src.renderer import Renderer
except ModuleNotFoundError:
    print("Error: found missing modules."
          " Run 'make install' before run the program", file=sys.stderr)
    sys.exit(1)

try:
    from mazegenerator import MazeGenerator
except ModuleNotFoundError:
    print("Error: Missing module 'mazegenerator'", file=sys.stderr)
    sys.exit(1)


def strip_comments(content: str) -> str:
    """Elimina lineas comentadas con '#' segun la seccion V.2 del subject."""
    lines = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped.startswith("#"):
            lines.append(line)
    return "\n".join(lines)


def load_config(file_path_str: str) -> Pacman_Parser:
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
            print(f"Warning: Corrupted JSON syntax ({err}). "
                  f"Fallback to default values.", file=sys.stderr)
            data = {}

        return Pacman_Parser.model_validate(data)

    except FileNotFoundError:
        sys.exit(f"Error: The configuration file '{path}' was not found.")
    except PermissionError:
        sys.exit(f"Error: Permission denied to read the file '{path}'.")
    except ValidationError as e:
        sys.exit(f"Error: Invalid configuration data.\n{e}")
    except UnicodeDecodeError:
        sys.exit("Error: Could not read file: invalid UTF-8 sequence.")
    except Exception as e:
        sys.exit(f"Error: An unexpected error occurred: {e}")


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("Error: Invalid number of arguments.\nUsage: "
                 "python3 pac-man.py <config.json>")

    game = load_config(sys.argv[1])
    print("Configuration loaded successfully.")
    print(f"Highscore File: {game.highscore_filename} | Lives: {game.lives}\n")

    # Loop through the validated list of LevelConfig objects
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
            sys.exit(f"Error: MazeGenerator failed on "
                     f"level {level.level_id}: {e}")

        mazes.append(maze_gen.maze)
    try:
        renderer = Renderer(game, mazes)
        renderer.run()
    except KeyboardInterrupt:
        print("\nExiting program...")


if __name__ == "__main__":
    main()
