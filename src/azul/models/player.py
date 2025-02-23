"""Module containing the Player class for the Azul game."""

from dataclasses import dataclass, field
from typing import List, Optional

from .tile import Tile


@dataclass
class Player:
    """Represents a player in the Azul game.

    Attributes:
        name: The name of the player
        pattern_lines: List of pattern lines, each containing tiles
        wall: The player's wall, a 2D grid of placed tiles
        floor_line: List of penalty tiles
        score: The player's current score
    """

    name: str
    board_size: int = 5
    pattern_lines: List[List[Tile]] = field(init=False)
    wall: List[List[Optional[str]]] = field(init=False)
    floor_line: List[Tile] = field(init=False)
    score: int = field(default=0)

    def __post_init__(self) -> None:
        """Initialize the player's board after creation."""
        self.pattern_lines = [[] for _ in range(self.board_size)]
        self.wall = [
            [None for _ in range(self.board_size)] for _ in range(self.board_size)
        ]
        self.floor_line = []
