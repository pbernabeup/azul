"""AI player implementation for the Azul game."""

from typing import TYPE_CHECKING, Optional, Tuple

from .models import Player, Source

if TYPE_CHECKING:
    from .game import AzulGame


class AzulCPU:
    """AI player implementation with different strategies."""

    def __init__(self, game: "AzulGame", algorithm: str):
        """Initialize the AI player.

        Args:
            game: The game instance this AI is playing in
            algorithm: The AI strategy to use ('dummy', 'greedy', 'smart', 'strategic')
        """
        self.game = game
        self.algorithm = algorithm

    def choose_move(self) -> Tuple[Source, str, int]:
        """Choose the next move based on the selected algorithm.

        Returns:
            Tuple of (chosen_source, chosen_color, chosen_line)
        """
        if self.algorithm == "dummy":
            return self.dummy_algorithm()
        elif self.algorithm == "greedy":
            return self.greedy_algorithm()
        elif self.algorithm == "smart":
            return self.smart_algorithm()
        elif self.algorithm == "strategic":
            return self.strategic_algorithm()
        raise ValueError(f"Unknown algorithm: {self.algorithm}")

    def dummy_algorithm(self) -> Tuple[Source, str, int]:
        """Choose first available source and color, and widest valid line."""
        player = self.game.players[self.game.active_player]
        sources = self.game.factories + (
            [self.game.center] if self.game.is_center_valid_choice() else []
        )

        for source in sources:
            for color in set(tile.color for tile in source.tiles if tile.color != "1"):
                valid_lines = self.game.logic.get_valid_lines(
                    player, color, self.game.mode, self.game.wall_pattern
                )
                if valid_lines:
                    return source, color, max(valid_lines)

        # If no valid moves found, try to minimize negative points
        return self.find_least_negative()

    def greedy_algorithm(self) -> Tuple[Source, str, int]:
        """Greedy AI logic: maximize immediate tile placement."""
        best_move = None
        largest = 0
        least = float("inf")
        player = self.game.players[self.game.active_player]

        for source in self.game.factories + [self.game.center]:
            for color in set(tile.color for tile in source.tiles if tile.color != "1"):
                tiles = [tile for tile in source.tiles if tile.color == color]
                for line_index in self.game.logic.get_valid_lines(
                    player, color, self.game.mode, self.game.wall_pattern
                ):
                    spaces = line_index + 1 - len(player.pattern_lines[line_index])
                    if len(tiles) <= spaces:
                        if len(tiles) > largest:
                            largest = len(tiles)
                            best_move = (source, color, line_index)
                            least = 0
                        elif least != 0:
                            tiles_too_many = abs(spaces - len(tiles))
                            if tiles_too_many < least:
                                least = tiles_too_many
                                best_move = (source, color, line_index)

        if not best_move:
            best_move = self.find_least_negative()

        return best_move

    def smart_algorithm(self) -> Tuple[Source, str, int]:
        """Smart AI logic: prioritize adjacent placements and minimize whitespace."""
        best_move = None
        least_whitespace = float("inf")
        most_tiles = 0
        move_found = False
        one_adjacent_move = False
        player = self.game.players[self.game.active_player]

        for source in self.game.factories + [self.game.center]:
            for color in set(tile.color for tile in source.tiles if tile.color != "1"):
                tiles = [tile for tile in source.tiles if tile.color == color]
                for line_index in self.game.logic.get_valid_lines(
                    player, color, self.game.mode, self.game.wall_pattern
                ):
                    spaces = line_index + 1 - len(player.pattern_lines[line_index])
                    if len(tiles) <= spaces:
                        move_found = True
                        whitespace = spaces - len(tiles)
                        if whitespace <= least_whitespace:
                            if whitespace < least_whitespace:
                                least_whitespace = whitespace
                                one_adjacent_move = False
                                most_tiles = 0

                            if not one_adjacent_move:
                                if self.has_adjacent(player, line_index, color):
                                    one_adjacent_move = True
                                    best_move = (source, color, line_index)
                                elif len(tiles) > most_tiles:
                                    best_move = (source, color, line_index)
                                    most_tiles = len(tiles)

        if not move_found:
            best_move = self.find_least_overflow(player)

        if not best_move:
            best_move = self.find_least_negative()

        return best_move

    def strategic_algorithm(self) -> Tuple[Source, str, int]:
        """Strategic AI logic: prioritize diagonal moves in first round, then adjacent placements."""
        best_move = None
        least_whitespace = float("inf")
        most_tiles = 0
        move_found = False
        diagonal_move = False
        one_adjacent_move = False
        two_adjacent_move = False
        player = self.game.players[self.game.active_player]

        for source in self.game.factories + [self.game.center]:
            for color in set(tile.color for tile in source.tiles if tile.color != "1"):
                tiles = [tile for tile in source.tiles if tile.color == color]
                for line_index in self.game.logic.get_valid_lines(
                    player, color, self.game.mode, self.game.wall_pattern
                ):
                    spaces = line_index + 1 - len(player.pattern_lines[line_index])
                    if len(tiles) <= spaces:
                        move_found = True
                        whitespace = spaces - len(tiles)
                        if whitespace <= least_whitespace:
                            if whitespace < least_whitespace:
                                least_whitespace = whitespace
                                diagonal_move = two_adjacent_move = (
                                    one_adjacent_move
                                ) = False
                                most_tiles = 0

                            if not diagonal_move:
                                if self.game.round_num == 1:
                                    if self.is_move_in_diagonal(line_index, color):
                                        best_move = (source, color, line_index)
                                        diagonal_move = True
                                if not two_adjacent_move:
                                    adj_horizontal, adj_vertical = self.check_adjacents(
                                        player, line_index, color
                                    )
                                    if adj_horizontal and adj_vertical:
                                        best_move = (source, color, line_index)
                                        two_adjacent_move = True
                                if not two_adjacent_move and not one_adjacent_move:
                                    adj_horizontal, adj_vertical = self.check_adjacents(
                                        player, line_index, color
                                    )
                                    if adj_horizontal or adj_vertical:
                                        best_move = (source, color, line_index)
                                        one_adjacent_move = True
                                    elif len(tiles) > most_tiles:
                                        best_move = (source, color, line_index)
                                        most_tiles = len(tiles)

        if not move_found:
            best_move = self.find_least_overflow(player)

        if not best_move:
            best_move = self.find_least_negative()

        return best_move

    def find_least_overflow(self, player: Player) -> Optional[Tuple[Source, str, int]]:
        """Find move that minimizes overflow tiles."""
        best_move = None
        least = float("inf")

        for source in self.game.factories + [self.game.center]:
            for color in set(tile.color for tile in source.tiles if tile.color != "1"):
                tiles = [tile for tile in source.tiles if tile.color == color]
                for line_index in self.game.logic.get_valid_lines(
                    player, color, self.game.mode, self.game.wall_pattern
                ):
                    spaces = line_index + 1 - len(player.pattern_lines[line_index])
                    tiles_too_many = abs(spaces - len(tiles))
                    if tiles_too_many < least:
                        least = tiles_too_many
                        best_move = (source, color, line_index)

        return best_move

    def find_least_negative(self) -> Tuple[Source, str, int]:
        """Find move that minimizes floor line tiles."""
        min_floor_tiles = float("inf")
        best_move = None
        sources = self.game.factories + (
            [self.game.center] if self.game.is_center_valid_choice() else []
        )

        for source in sources:
            for color in set(tile.color for tile in source.tiles if tile.color != "1"):
                tiles = [tile for tile in source.tiles if tile.color == color]
                if len(tiles) < min_floor_tiles:
                    min_floor_tiles = len(tiles)
                    best_move = (source, color, -1)

        if best_move is None:
            raise RuntimeError("No valid moves available")
        return best_move

    def has_adjacent(self, player: Player, line_index: int, color: str) -> bool:
        """Check if a tile placement would be adjacent to existing tiles."""
        if self.game.mode == "pattern":
            col = self.game.wall_pattern[line_index].index(color)
        else:
            col = next(
                (
                    j
                    for j in range(5)
                    if player.wall[line_index][j] is None
                    and all(player.wall[k][j] != color for k in range(5))
                ),
                None,
            )
            if col is None:
                return False

        adj_horizontal, adj_vertical = self.check_adjacents(
            player, line_index, color, col
        )
        return adj_horizontal or adj_vertical

    def check_adjacents(
        self, player: Player, row: int, color: str, col: Optional[int] = None
    ) -> Tuple[bool, bool]:
        """Check for horizontally and vertically adjacent tiles."""
        if col is None:
            if self.game.mode == "pattern":
                col = self.game.wall_pattern[row].index(color)
            else:
                try:
                    col = next(
                        j
                        for j in range(5)
                        if player.wall[row][j] is None
                        and all(player.wall[k][j] != color for k in range(5))
                    )
                except StopIteration:
                    return False, False

        horizontal = (col > 0 and player.wall[row][col - 1]) or (
            col < 4 and player.wall[row][col + 1]
        )
        vertical = (row > 0 and player.wall[row - 1][col]) or (
            row < 4 and player.wall[row + 1][col]
        )

        return horizontal, vertical

    def is_move_in_diagonal(self, line: int, color: str) -> bool:
        """Check if placing the given color on the given line would be a diagonal move."""
        if self.game.mode == "pattern":
            return line == self.game.wall_pattern[line].index(color)
        else:
            return line == color
