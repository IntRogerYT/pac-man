import re
import random
from typing import List, Any
from pydantic import BaseModel, ConfigDict, model_validator


class LevelConfig(BaseModel):
    """Validated configuration for a single level."""
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
        """Clamp and sanitize level values before validation."""
        if not isinstance(data, dict):
            data = {}

        def get_int(key: str, default: int, min_val: int, max_val: int) -> int:
            """Return an int clamped to the given bounds, or the default."""
            val = data.get(key, default)
            try:
                val = int(val)
                if val < min_val:
                    print(f"Warning: {key} ({val}) is below minimum "
                          f"{min_val}. Clamping to {min_val}.")
                    return min_val
                if val > max_val:
                    print(f"Warning: {key} ({val}) is above the maximum "
                          f"{max_val}. Clamping to {max_val}.")
                    return max_val
                return val
            except (ValueError, TypeError):
                print(f"Warning: Invalid or missing type for {key}. "
                      f"Clamping to default {default}.")
                return default

        data['level_id'] = get_int(
            'level_id', default=1, min_val=1, max_val=100)
        data['width'] = get_int('width', default=15, min_val=5, max_val=42)
        data['height'] = get_int('height', default=15, min_val=5, max_val=42)
        data['level_max_time'] = get_int('level_max_time',
                                         default=142, min_val=42, max_val=999)
        data['pacgum'] = get_int('pacgum', default=0, min_val=0, max_val=(
            data['width']*data['height'])-5)

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
            data['seed'] = random.randint(0, 2**64 - 1)

        return data


class Pacman_Parser(BaseModel):
    """Validated top-level game configuration."""
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
        """Clamp and sanitize global settings before validation."""
        if not isinstance(data, dict):
            print("Warning: Configuration is not a valid "
                  "JSON object. Using all default values.")
            data = {}

        def get_int(
                key: str, default: int, min_val: int = 0, max_val: int = 100000
                ) -> int:
            """Return an int clamped to the given bounds, or the default."""
            val = data.get(key, default)
            try:
                val = int(val)
                if val < min_val:
                    print(f"Warning: {key} ({val}) is below "
                          f"minimum {min_val}. Clamping to {min_val}.")
                    return min_val
                if val > max_val:
                    print(f"Warning: {key} ({val}) is above the maximum "
                          f"{max_val}. Clamping to {max_val}.")
                    return max_val
                return val
            except (ValueError, TypeError):
                print(f"Warning: Invalid or missing type for {key}. "
                      f"Clamping to default {default}.")
                return default

        data['lives'] = get_int('lives', default=3, min_val=1, max_val=999)
        data['points_per_pacgum'] = get_int('points_per_pacgum',
                                            default=10,
                                            min_val=0, max_val=1000)
        data['points_per_super_pacgum'] = get_int('points_per_super_pacgum',
                                                  default=50,
                                                  min_val=0, max_val=10000)
        data['points_per_ghost'] = get_int('points_per_ghost',
                                           default=200,
                                           min_val=0, max_val=100000)

        hs_file = str(data.get('highscore_filename', 'scores.txt'))
        if not re.match(r'^[a-zA-Z0-9_-]+\.[a-zA-Z0-9]+$', hs_file):
            print(f"Warning: Invalid highscore filename '{hs_file}'. "
                  f"Clamping to 'scores.txt'.")
            data['highscore_filename'] = 'scores.txt'
        else:
            data['highscore_filename'] = hs_file

        if not (data['points_per_ghost'] >
                data['points_per_super_pacgum'] > data['points_per_pacgum']):
            print("Warning: Points hierarchy invalid. "
                  "Enforcing default hierarchy (200 > 50 > 10).")
            data['points_per_ghost'] = 200
            data['points_per_super_pacgum'] = 50
            data['points_per_pacgum'] = 10

        levels_data = data.get('levels', [])
        if not isinstance(levels_data, list):
            print("Warning: 'levels' is missing or not an array. "
                  "Generating default levels.")
            levels_data = []

        if len(levels_data) < 10:
            missing = 10 - len(levels_data)
            print(f"Warning: Found {len(levels_data)} levels. "
                  f"The project requires at least 10. Generating "
                  f"{missing} missing levels.")
            for _ in range(missing):
                levels_data.append({})

        def _get_level_id_sort_key(lvl: object) -> float:
            "Get the level id to sort later"
            if isinstance(lvl, dict):
                lid = lvl.get("level_id")
                if isinstance(lid, int):
                    return float(lid)
            return float("inf")

        sorted_levels = sorted(levels_data, key=_get_level_id_sort_key)

        processed_levels = []
        expected_id = 1
        for lvl in sorted_levels:
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
