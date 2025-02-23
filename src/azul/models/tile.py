"""Module containing the Tile class for the Azul game."""

from dataclasses import dataclass


@dataclass
class Tile:
    """Represents a single tile in the Azul game.

    Attributes:
        color: The color of the tile, represented as a single character:
               'R' for Red, 'B' for Blue, 'Y' for Yellow,
               'K' for Black, 'W' for White, '1' for First Player Token
    """

    color: str
