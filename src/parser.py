import re
import random
from typing import List, Any
from pydantic import BaseModel, ConfigDict, model_validator


class LevelConfig(BaseModel):
    # Unknown keys must be ignored
    model_config = ConfigDict(extra='ignore')

    level_id: int
    width: int
    height: int
    level_max_time: int
    pacgum: int
    seed: int

    @model_validator(mode='before')
    @classmethod
    def clamp_level_values(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            data = {}

        # Helper to clamp integer values safely
        def get_int(key: str, default: int, min_val: int) -> int:
            val = data.get(key, default)
            try:
                val = int(val)
                if val < min_val:
                    print(f"Warning: {key} ({val}) is below minimum "
                          f"{min_val}. Clamping to {min_val}.")
                    return min_val
                return val
            except (ValueError, TypeError):
                print(f"Warning: Invalid or missing type for {key}. "
                      f"Clamping to default {default}.")
                return default

        data['level_id'] = get_int('level_id', default=1, min_val=1)
        data['width'] = get_int('width', default=15, min_val=5)
        data['height'] = get_int('height', default=15, min_val=5)
        data['level_max_time'] = get_int('level_max_time',
                                         default=142, min_val=42)
        data['pacgum'] = get_int('pacgum', default=0, min_val=0)

        # Pacgum Limit Check
        max_tiles = data['width'] * data['height']
        if data['pacgum'] >= max_tiles:
            clamped_pacgum = max(0, max_tiles - 1)
            print(f"Warning: Pacgum ({data['pacgum']}) exceeds max "
                  f"tiles for {data['width']}x{data['height']}. "
                  f"Clamping to {clamped_pacgum}.")
            data['pacgum'] = clamped_pacgum

        if 'seed' in data and data['seed'] is not None:
            try:
                data['seed'] = int(data['seed'])
            except (ValueError, TypeError):
                rand_seed = random.randint(0, 2**64 - 1)
                print(f"Warning: Invalid seed for level "
                      f"{data.get('level_id', '?')}. "
                      f"Generated random seed: {rand_seed}.")
                data['seed'] = rand_seed
        else:
            # Si no se especifica en el JSON, se genera aleatoria
            data['seed'] = random.randint(0, 2**64 - 1)

        return data


class Pacman_Parser(BaseModel):
    # Unknown keys must be ignored
    model_config = ConfigDict(extra='ignore')

    highscore_filename: str
    lives: int
    points_per_pacgum: int
    points_per_super_pacgum: int
    points_per_ghost: int
    levels: List[LevelConfig]

    @model_validator(mode='before')
    @classmethod
    def clamp_global_values(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            print("Warning: Configuration is not a valid "
                  "JSON object. Using all default values.")
            data = {}

        def get_int(key: str, default: int, min_val: int = 0) -> int:
            val = data.get(key, default)
            try:
                val = int(val)
                if val < min_val:
                    print(f"Warning: {key} ({val}) is below "
                          f"minimum {min_val}. Clamping to {min_val}.")
                    return min_val
                return val
            except (ValueError, TypeError):
                print(f"Warning: Invalid or missing type for {key}. "
                      f"Clamping to default {default}.")
                return default

        # Global basic fields
        data['lives'] = get_int('lives', default=3, min_val=1)
        data['points_per_pacgum'] = get_int('points_per_pacgum',
                                            default=10, min_val=0)
        data['points_per_super_pacgum'] = get_int('points_per_super_pacgum',
                                                  default=50, min_val=0)
        data['points_per_ghost'] = get_int('points_per_ghost',
                                           default=200, min_val=0)

        # Highscore filename handling
        hs_file = str(data.get('highscore_filename', 'scores.txt'))
        if not re.match(r'^[a-zA-Z0-9_-]+\.[a-zA-Z0-9]+$', hs_file):
            print(f"Warning: Invalid highscore filename '{hs_file}'. "
                  f"Clamping to 'scores.txt'.")
            data['highscore_filename'] = 'scores.txt'

        # Points Hierarchy Check
        if not (data['points_per_ghost'] >
                data['points_per_super_pacgum'] > data['points_per_pacgum']):
            print("Warning: Points hierarchy invalid. "
                  "Enforcing default hierarchy (200 > 50 > 10).")
            data['points_per_ghost'] = 200
            data['points_per_super_pacgum'] = 50
            data['points_per_pacgum'] = 10

        # Process Levels array
        levels_data = data.get('levels', [])
        if not isinstance(levels_data, list):
            print("Warning: 'levels' is missing or not an array. "
                  "Generating default levels.")
            levels_data = []

        # Enforce Minimum 10 Levels (Subject Requirement)
        if len(levels_data) < 10:
            missing = 10 - len(levels_data)
            print(f"Warning: Found {len(levels_data)} levels. "
                  f"The project requires at least 10. Generating "
                  f"{missing} missing levels.")
            for _ in range(missing):
                # Empty dict forces LevelConfig to use defaults
                levels_data.append({})

        # Enforce strict sequential IDs (1 to N)
        processed_levels = []
        expected_id = 1
        for lvl in levels_data:
            if not isinstance(lvl, dict):
                lvl = {}
            if lvl.get('level_id') != expected_id:
                if 'level_id' in lvl:
                    print(f"Warning: Level ID {lvl.get('level_id')} "
                          f"out of sequence or duplicate. "
                          f"Clamping to {expected_id}.")
                lvl['level_id'] = expected_id

            processed_levels.append(lvl)
            expected_id += 1

        data['levels'] = processed_levels

        return data
