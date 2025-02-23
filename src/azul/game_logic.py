"""Module containing the game logic for Azul."""

from typing import List, Optional, Tuple

from .models import Player


class GameLogic:
    """Handles the game logic for Azul, including scoring and validation."""

    FLOOR_PENALTIES = [1, 1, 2, 2, 2, 3, 3]  # Points lost for each floor line position

    @staticmethod
    def score_tile(player: Player, row: int, col: int) -> int:
        """Calculate the score for placing a tile.

        Args:
            player: The player who placed the tile
            row: The row where the tile was placed
            col: The column where the tile was placed

        Returns:
            The score for this tile placement
        """
        score = 1
        horizontal_connection = False
        vertical_connection = False

        # Check horizontal
        left = right = col
        while left > 0 and player.wall[row][left - 1]:
            left -= 1
            score += 1
            horizontal_connection = True
        while right < 4 and player.wall[row][right + 1]:
            right += 1
            score += 1
            horizontal_connection = True

        # Check vertical
        up = down = row
        while up > 0 and player.wall[up - 1][col]:
            up -= 1
            score += 1
            vertical_connection = True
        while down < 4 and player.wall[down + 1][col]:
            down += 1
            score += 1
            vertical_connection = True

        # If no connections, score is just 1
        if not horizontal_connection and not vertical_connection:
            return 1

        return score

    @staticmethod
    def calculate_end_game_bonus(player: Player) -> Tuple[int, int, int]:
        """Calculate end-game bonus points.

        Args:
            player: The player to calculate bonus points for

        Returns:
            Tuple of (complete_rows, complete_columns, complete_colors)
        """
        complete_rows = sum(
            1 for row in player.wall if all(cell is not None for cell in row)
        )
        complete_cols = sum(
            1 for col in range(5) if all(row[col] is not None for row in player.wall)
        )
        complete_colors = sum(
            1
            for color in ["R", "B", "Y", "K", "W"]
            if sum(row.count(color) for row in player.wall) == 5
        )

        return complete_rows * 2, complete_cols * 7, complete_colors * 10

    @staticmethod
    def get_valid_lines(
        player: Player,
        color: str,
        mode: str = "pattern",
        wall_pattern: Optional[List[List[str]]] = None,
    ) -> List[int]:
        """Get valid pattern lines for a tile placement.

        Args:
            player: The player making the move
            color: The color of the tile being placed
            mode: The game mode ('pattern' or 'free')
            wall_pattern: The wall pattern for pattern mode

        Returns:
            List of valid line indices
        """
        valid_lines = []
        for i, line in enumerate(player.pattern_lines):
            if len(line) == 0 or (line[0].color == color and len(line) < i + 1):
                if mode == "pattern":
                    if color not in player.wall[i]:
                        valid_lines.append(i)
                else:
                    if color not in player.wall[i] and all(
                        player.wall[i][j] != color for j in range(5)
                    ):
                        valid_lines.append(i)
        return valid_lines

    @staticmethod
    def calculate_floor_penalty(num_tiles: int) -> int:
        """Calculate penalty points for floor line tiles.

        Args:
            num_tiles: Number of tiles in the floor line

        Returns:
            Number of penalty points
        """
        return sum(GameLogic.FLOOR_PENALTIES[:num_tiles])
