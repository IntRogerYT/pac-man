from src.parser import Pacman_Parser


def main() -> None:
    from pathlib import Path
    json_texto = Path('data/config.json').read_text(encoding='utf-8')

    game = Pacman_Parser.model_validate_json(json_texto)
    print(game)
    print(game.highscore_filename)
    # print(game.model_dump())


if __name__ == "__main__":
    main()
