from pathlib import Path
from src.parser import Pacman_Parser
from mazegenerator import MazeGenerator
from src.renderer import Renderer


def main() -> None:
    # 1. Read and validate the JSON configuration
    json_text = Path('config.json').read_text(encoding='utf-8')
    game = Pacman_Parser.model_validate_json(json_text)

    print("Configuration loaded successfully.")
    print(f"Highscore File: {game.highscore_filename} | Lives: "
          f"{game.lives} | Global Seed: {game.seed}\n")

    # 2. Loop through the validated list of LevelConfig objects
    mazes = []
    for level in game.levels:
        print(f"=== Generating Level {level.level_id} ===")
        print(f"Dimensions: {level.width}x"
              f"{level.height} | Max Time: {level.level_max_time}s")

        # 3. Instantiate the generator using the specific level dimensions
        maze_gen = MazeGenerator(
            size=(level.width, level.height),
            seed=game.seed
        )

        # 4. Execute the algorithm
        maze_gen.generate()

        # 5. Output the result for verification
        print(maze_gen.maze)
        print("\n")
        mazes.append(maze_gen.maze)

    renderer = Renderer(game, mazes[0])
    renderer.main_menu()


if __name__ == "__main__":
    main()
