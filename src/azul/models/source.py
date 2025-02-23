"""Module containing the Source class for the Azul game."""

from dataclasses import dataclass, field
from typing import List

from .tile import Tile


@dataclass
class Source:
    """Represents a source of tiles in the Azul game.

    A source can be either a factory or the center of the table.

    Attributes:
        name: The name of the source (e.g., "Factory 1", "Center")
        tiles: List of tiles currently in this source
    """

    name: str
    tiles: List[Tile] = field(default_factory=list)

    def get_colors(self) -> List[str]:
        """Get unique colors in this source, excluding first player tile."""
        return list(set(tile.color for tile in self.tiles if tile.color != "1"))

    def count_color(self, color: str) -> int:
        """Count how many tiles of a given color are in this source."""
        return sum(1 for tile in self.tiles if tile.color == color)
