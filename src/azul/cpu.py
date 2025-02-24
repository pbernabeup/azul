"""AI player implementation for the Azul game."""

from copy import deepcopy
from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from .models import Player, Source, Tile

if TYPE_CHECKING:
    from .game import AzulGame


@dataclass
class GameState:
    """Lightweight game state representation to avoid deep copying."""

    pattern_lines: List[List[str]]  # Just store colors instead of full Tile objects
    wall: List[List[Optional[str]]]
    floor_line: int  # Just store count instead of full list
    score: int

    @classmethod
    def from_player(cls, player: Player) -> "GameState":
        """Create GameState from a Player object."""
        return cls(
            pattern_lines=[[t.color for t in line] for line in player.pattern_lines],
            wall=[[cell for cell in row] for row in player.wall],
            floor_line=len(player.floor_line),
            score=player.score,
        )


class AzulCPU:
    """AI player implementation with different strategies."""

    def __init__(self, game: "AzulGame", algorithm: str):
        """Initialize the AI player.

        Args:
            game: The game instance this AI is playing in
            algorithm: The AI strategy to use ('dummy', 'greedy', 'smart', 'strategic', 'minmax')
        """
        self.game = game
        self.algorithm = algorithm
        # Cache wall pattern indices for faster lookups
        self.wall_pattern_indices = {}
        if game.mode == "pattern":
            for i, row in enumerate(game.wall_pattern):
                for color in set(row):
                    self.wall_pattern_indices[(i, color)] = row.index(color)

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
        elif self.algorithm == "minmax":
            return self.minmax_algorithm()
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

    def evaluate_state(self, player: Player, opponent: Player) -> float:
        """Evaluate the current game state from player's perspective.

        Args:
            player: The player to evaluate
            opponent: The opponent player

        Returns:
            Score differential between player and opponent
        """
        # Calculate immediate points from wall tiles
        player_score = 0
        opponent_score = 0

        # Score existing wall tiles
        for row in range(5):
            for col in range(5):
                if player.wall[row][col]:
                    player_score += self.game.logic.score_tile(player, row, col)
                if opponent.wall[row][col]:
                    opponent_score += self.game.logic.score_tile(opponent, row, col)

        # Add potential points from pattern lines
        for i, line in enumerate(player.pattern_lines):
            if len(line) == i + 1:  # Line is complete
                if self.game.mode == "pattern":
                    col = self.game.wall_pattern[i].index(line[0].color)
                    if not player.wall[i][col]:
                        player_score += self.game.logic.score_tile(player, i, col)

        for i, line in enumerate(opponent.pattern_lines):
            if len(line) == i + 1:  # Line is complete
                if self.game.mode == "pattern":
                    col = self.game.wall_pattern[i].index(line[0].color)
                    if not opponent.wall[i][col]:
                        opponent_score += self.game.logic.score_tile(opponent, i, col)

        # Subtract floor penalties
        player_score -= self.game.logic.calculate_floor_penalty(len(player.floor_line))
        opponent_score -= self.game.logic.calculate_floor_penalty(
            len(opponent.floor_line)
        )

        # Add end game bonuses if close to end
        if self.is_near_game_end(player) or self.is_near_game_end(opponent):
            p_rows, p_cols, p_colors = self.game.logic.calculate_end_game_bonus(player)
            o_rows, o_cols, o_colors = self.game.logic.calculate_end_game_bonus(
                opponent
            )
            player_score += p_rows + p_cols + p_colors
            opponent_score += o_rows + o_cols + o_colors

        return player_score - opponent_score

    def is_near_game_end(self, player: Player) -> bool:
        """Check if player is close to ending the game."""
        # Check if any row is complete or nearly complete
        for row in player.wall:
            filled = sum(1 for cell in row if cell is not None)
            if filled >= 4:  # Row is complete or one tile away
                return True
        return False

    def simulate_move(
        self, source: Source, color: str, line: int, player: Player
    ) -> Tuple[Player, List[Tile]]:
        """Simulate a move without modifying the actual game state.

        Args:
            source: The source to take tiles from
            color: The color to take
            line: The pattern line to place tiles in (-1 for floor)
            player: The player making the move

        Returns:
            Tuple of (updated player state, remaining tiles)
        """
        # Create deep copies to avoid modifying original state
        player = deepcopy(player)
        remaining_tiles = []

        # Get tiles of chosen color
        chosen_tiles = [tile for tile in source.tiles if tile.color == color]

        # Get other tiles that will go to floor
        other_tiles = [tile for tile in source.tiles if tile.color != color]
        if other_tiles:
            remaining_tiles.extend(other_tiles)

        # Place tiles in pattern line or floor
        if line >= 0:
            spaces = line + 1 - len(player.pattern_lines[line])
            if spaces > 0:
                # Place what fits in the pattern line
                to_place = chosen_tiles[:spaces]
                player.pattern_lines[line].extend(to_place)
                # Rest goes to floor
                if len(chosen_tiles) > spaces:
                    player.floor_line.extend(chosen_tiles[spaces:])
            else:
                # All tiles go to floor
                player.floor_line.extend(chosen_tiles)
        else:
            # All tiles go to floor
            player.floor_line.extend(chosen_tiles)

        return player, remaining_tiles

    def get_possible_moves(
        self, player: Player, sources: List[Source]
    ) -> List[Tuple[Source, str, int]]:
        """Get all possible moves for a player.

        Args:
            player: The player to get moves for
            sources: List of available sources

        Returns:
            List of possible moves as (source, color, line) tuples
        """
        moves = []
        for source in sources:
            for color in set(tile.color for tile in source.tiles if tile.color != "1"):
                # Try each valid pattern line
                valid_lines = self.game.logic.get_valid_lines(
                    player, color, self.game.mode, self.game.wall_pattern
                )
                for line in valid_lines:
                    moves.append((source, color, line))
                # Always possible to place in floor line
                moves.append((source, color, -1))
        return moves

    def evaluate_state_fast(
        self, player_state: GameState, opponent_state: GameState
    ) -> float:
        """Fast evaluation of game state."""
        score_diff = player_state.score - opponent_state.score

        # Penalize floor line tiles
        score_diff -= sum(self.game.logic.FLOOR_PENALTIES[: player_state.floor_line])
        score_diff += sum(self.game.logic.FLOOR_PENALTIES[: opponent_state.floor_line])

        # Quick estimate of potential points from pattern lines
        for i, line in enumerate(player_state.pattern_lines):
            if len(line) == i + 1 and line[0] != "1":  # Complete line
                score_diff += i + 2  # Approximate score

        for i, line in enumerate(opponent_state.pattern_lines):
            if len(line) == i + 1 and line[0] != "1":  # Complete line
                score_diff -= i + 2  # Approximate score

        return score_diff

    def get_efficient_moves(
        self, state: GameState, sources: List[Source]
    ) -> List[Tuple[Source, str, int, int]]:
        """Get promising moves for the AI player by filtering out obviously suboptimal choices.

        Analyzes the current game state to identify moves that are likely to score well,
        eliminating moves that would obviously waste tiles or result in penalties.

        Returns:
            list[tuple]: List of (source, color, line, num_tiles) tuples where:
                - source: The factory/center to take tiles from
                - color: The color of tiles to take
                - line: The pattern line to place tiles in
                - num_tiles: Number of tiles to move
        """
        moves = []
        for source in sources:
            # Get available colors and their counts
            color_counts: Dict[str, int] = {}
            for tile in source.tiles:
                if tile.color != "1":
                    color_counts[tile.color] = color_counts.get(tile.color, 0) + 1

            for color, count in color_counts.items():
                # Try each valid pattern line
                if self.game.mode == "pattern":
                    for i in range(5):
                        if not state.wall[i][
                            self.wall_pattern_indices.get((i, color), 0)
                        ] and (  # Space on wall
                            not state.pattern_lines[i]  # Empty line
                            or (
                                state.pattern_lines[i][0] == color  # Same color
                                and len(state.pattern_lines[i]) < i + 1
                            )
                        ):  # Not full
                            moves.append((source, color, i, count))
                else:
                    # Similar logic for free mode...
                    pass

                # Only consider floor line if no valid pattern lines or very few tiles
                if not moves or count <= 2:
                    moves.append((source, color, -1, count))

        return moves

    def simulate_move_fast(
        self, state: GameState, color: str, line: int, num_tiles: int
    ) -> GameState:
        """Fast simulation of a move using simplified state."""
        # Create new state with list comprehension instead of deepcopy
        new_state = GameState(
            pattern_lines=[line[:] for line in state.pattern_lines],
            wall=[[cell for cell in row] for row in state.wall],
            floor_line=state.floor_line,
            score=state.score,
        )

        if line >= 0:
            spaces = line + 1 - len(new_state.pattern_lines[line])
            if spaces > 0:
                # Add tiles to pattern line
                tiles_to_place = min(spaces, num_tiles)
                new_state.pattern_lines[line].extend([color] * tiles_to_place)
                # Rest goes to floor
                if num_tiles > spaces:
                    new_state.floor_line += num_tiles - spaces
            else:
                new_state.floor_line += num_tiles
        else:
            new_state.floor_line += num_tiles

        return new_state

    def minmax_algorithm(self) -> Tuple[Source, str, int]:
        """Optimized minmax AI logic using opponent's actual strategy."""
        from .game import AzulGame  # Lazy import to avoid circular dependency

        player = self.game.players[self.game.active_player]
        opponent_idx = (self.game.active_player + 1) % len(self.game.players)
        opponent = self.game.players[opponent_idx]
        opponent_ai = self.game.ai[opponent_idx]

        if opponent_ai is None:  # Fallback for human opponents
            return self.strategic_algorithm()

        sources = self.game.factories + (
            [self.game.center] if self.game.is_center_valid_choice() else []
        )
        if not sources:
            return self.find_least_negative()

        best_move = None
        best_score = float("-inf")

        # Get efficient moves
        moves = self.get_efficient_moves(GameState.from_player(player), sources)

        for source, color, line, num_tiles in moves:
            # Create minimal copies of just the player states
            new_player = Player(player.name)
            new_player.pattern_lines = [
                [Tile(t.color) for t in line] for line in player.pattern_lines
            ]
            new_player.wall = [[cell for cell in row] for row in player.wall]
            new_player.floor_line = [Tile(t.color) for t in player.floor_line]
            new_player.score = player.score

            new_opponent = Player(opponent.name)
            new_opponent.pattern_lines = [
                [Tile(t.color) for t in line] for line in opponent.pattern_lines
            ]
            new_opponent.wall = [[cell for cell in row] for row in opponent.wall]
            new_opponent.floor_line = [Tile(t.color) for t in opponent.floor_line]
            new_opponent.score = opponent.score

            # Apply our move
            chosen_tiles = [
                Tile(color)
                for _ in range(sum(1 for t in source.tiles if t.color == color))
            ]
            other_tiles = [Tile(t.color) for t in source.tiles if t.color != color]

            if line >= 0:
                spaces = line + 1 - len(new_player.pattern_lines[line])
                if spaces > 0:
                    to_place = chosen_tiles[:spaces]
                    new_player.pattern_lines[line].extend(to_place)
                    if len(chosen_tiles) > spaces:
                        new_player.floor_line.extend(chosen_tiles[spaces:])
                else:
                    new_player.floor_line.extend(chosen_tiles)
            else:
                new_player.floor_line.extend(chosen_tiles)

            # Create minimal game state for opponent's turn
            new_sources = []
            for s in sources:
                if s != source:
                    new_source = Source(s.name)
                    new_source.tiles = [Tile(t.color) for t in s.tiles]
                    new_sources.append(new_source)
                elif other_tiles:  # If tiles went to center
                    new_center = Source("Center")
                    new_center.tiles = other_tiles
                    new_sources.append(new_center)

            # Create minimal game state
            temp_game = AzulGame(2, mode=self.game.mode, verbose=False)
            temp_game.players = [
                new_opponent,
                new_player,
            ]  # Note: Swapped order since opponent will be active
            temp_game.factories = [
                s for s in new_sources if s.name.startswith("Factory")
            ]
            temp_game.center = next(
                (s for s in new_sources if s.name == "Center"), Source("Center")
            )
            temp_game.wall_pattern = self.game.wall_pattern
            temp_game.active_player = 0  # Opponent's turn

            # Create new AI instance to avoid circular reference
            temp_opponent_ai = AzulCPU(temp_game, opponent_ai.algorithm)

            try:
                # Get opponent's move using their strategy
                o_source, o_color, o_line = temp_opponent_ai.choose_move()

                # Apply opponent's move
                temp_game.execute_move(new_opponent, o_source, o_color, o_line)

                # Evaluate resulting state
                score = self.evaluate_state(new_player, new_opponent)

                if score > best_score:
                    best_score = score
                    best_move = (source, color, line)

            except Exception:
                # If opponent's strategy fails, fall back to strategic evaluation
                score = self.evaluate_state_fast(
                    GameState.from_player(new_player),
                    GameState.from_player(new_opponent),
                )
                if score > best_score:
                    best_score = score
                    best_move = (source, color, line)

        return best_move if best_move else self.find_least_negative()
