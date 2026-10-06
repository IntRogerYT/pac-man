from pydantic import (BaseModel, Field,)  # ConfigDict,
# model_validator, field_validator)
from typing import List


class Pacman_Parser(BaseModel):
    # model_config = ConfigDict(extra='forbid') # ES util realmente?
    highscore_filename: str = Field(
        ...,
        description="Define the highscore filename"
    )
    level: List[List[List[int]]] = Field(
        ...,
        description="List of multiple levels"
    )
    width: List[List[int]] = Field(
        ...,
        description="Width of the maze (must be greater than 1)"
    )
    height: List[List[int]] = Field(
        ...,
        description="Height of the maze (must be greater than 1)"
    )
    lives: int = Field(
        gt=0,
        description="???"
    )
    pacgum: int = Field(
        gt=0,
        description="???"
    )
    points_per_pacgum: int = Field(
        gt=0,
        description="???"
    )
    points_per_super_pacgum: int = Field(
        gt=0,
        description="???"
    )
    points_per_ghost: int = Field(
        gt=0,
        description="???"
    )
    seed: int = Field(
        description="???"
    )
    level_max_time: int = Field(
        gt=0,
        description="???"
    )
    """
    @model_validator(mode='after')
    def validate_maze_logic(self) -> None:
        # w, h = self.width, self.height
        pass
    """
