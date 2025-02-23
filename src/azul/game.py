"""Main game module for Azul."""

import random
from typing import List, Optional, Tuple

from .cpu import AzulCPU
from .display import Display
from .game_logic import GameLogic
from .models import Player, Source, Tile


class AzulGame:
    """Main game class that coordinates the Azul game."""

    def __init__(self, num_players: int, mode: str = "pattern", verbose: bool = True):
        """Initialize a new game of Azul.

        Args:
            num_players: Number of players in the game
            mode: Game mode ('pattern' or 'free')
            verbose: Whether to display game state
        """
        self.players = [Player(f"Player {i+1}") for i in range(num_players)]
        self.ai: List[Optional[AzulCPU]] = [
            AzulCPU(self, "dummy") for _ in range(num_players)
        ]
        self.factories = [Source(f"Factory {i+1}") for i in range(num_players * 2 + 1)]
        self.center = Source("Center")
        self.bag: List[Tile] = []
        self.discard: List[Tile] = []

        self.round_num = 1
        self.active_player = 0
        self.first_player_token = 0
        self.mode = mode
        self.verbose = verbose
        self.display = Display()
        self.logic = GameLogic()
        self.colors = ["R", "B", "Y", "K", "W"]  # Red, Blue, Yellow, blacK, White

        # Initialize center with first player token
        self.center.tiles = [Tile("1")]

        if mode == "pattern":
            self.wall_pattern = [
                ["B", "Y", "R", "K", "W"],
                ["W", "B", "Y", "R", "K"],
                ["K", "W", "B", "Y", "R"],
                ["R", "K", "W", "B", "Y"],
                ["Y", "R", "K", "W", "B"],
            ]
        else:
            self.wall_pattern = [[None for _ in range(5)] for _ in range(5)]

    def setup_game(self) -> None:
        """Set up the initial game state."""
        self.bag = [Tile(color) for color in self.colors for _ in range(20)]
        random.shuffle(self.bag)
        for factory in self.factories:
            factory.tiles = [self.bag.pop() for _ in range(4) if self.bag]
        self.center.tiles = [Tile("1")]

    def play_game(self) -> List[Player]:
        """Play a complete game of Azul.

        Returns:
            List of players with their final scores
        """
        self.setup_game()
        while not self.is_game_over():
            if self.verbose:
                print(f"\nRound {self.round_num}")
            self.play_round()
            self.end_round()
            self.round_num += 1

        self.end_game_scoring()

        if self.verbose:
            winner = max(self.players, key=lambda p: p.score)
            print("Game Over!")
            for player in self.players:
                print(f"{player.name} final score: {player.score}")
            print(f"The winner is {winner.name} with {winner.score} points!")

        return self.players

    def play_round(self) -> None:
        """Play a single round of the game."""
        self.active_player = self.first_player_token
        while (
            any(factory.tiles for factory in self.factories)
            or self.is_center_valid_choice()
        ):
            player = self.players[self.active_player]
            if self.verbose:
                self.display.display_game_state(
                    self.players, self.factories, self.center
                )
            self.play_turn(player, is_ai=(self.ai[self.active_player] is not None))
            self.active_player = (self.active_player + 1) % len(self.players)

    def play_turn(self, player: Player, is_ai: bool = False) -> None:
        """Play a single turn for a player.

        Args:
            player: The player whose turn it is
            is_ai: Whether the player is AI-controlled
        """
        if self.verbose:
            print(f"\n{player.name}'s turn")

        if is_ai:
            ai_player = self.ai[self.active_player]
            if ai_player is None:
                raise ValueError("AI player is None but is_ai is True")
            chosen_source, chosen_color, chosen_line = ai_player.choose_move()
        else:
            chosen_source, chosen_color, chosen_line = self.get_user_input()

        self.execute_move(player, chosen_source, chosen_color, chosen_line)

        if self.verbose:
            self.display.display_turn_results(
                player, chosen_source, chosen_color, chosen_line
            )

    def get_user_input(self) -> Tuple[Source, str, int]:
        """Get input from a human player.

        Returns:
            Tuple of (chosen_source, chosen_color, chosen_line)
        """
        if self.verbose:
            self.display_options()

        chosen_source = self.get_user_source_choice()
        chosen_color = self.get_user_color_choice(chosen_source)
        valid_lines = self.logic.get_valid_lines(
            self.players[self.active_player], chosen_color, self.mode, self.wall_pattern
        )
        chosen_line = self.choose_pattern_line(valid_lines)

        return chosen_source, chosen_color, chosen_line

    def execute_move(
        self, player: Player, source: Source, color: str, line: int
    ) -> None:
        """Execute a player's move.

        Args:
            player: The player making the move
            source: The source to take tiles from
            color: The color of tiles to take
            line: The line to place tiles on (-1 for floor line)
        """
        # Take tiles
        taken_tiles = [tile for tile in source.tiles if tile.color == color]

        # Move remaining tiles to center or update center
        if source != self.center:
            self.center.tiles.extend(
                [tile for tile in source.tiles if tile.color != color]
            )
            source.tiles.clear()
        else:
            self.center.tiles = [
                tile for tile in self.center.tiles if tile.color != color
            ]

        # Handle first player token
        if source == self.center and any(
            tile.color == "1" for tile in self.center.tiles
        ):
            self.center.tiles = [
                tile for tile in self.center.tiles if tile.color != "1"
            ]
            self.first_player_token = self.players.index(player)
            player.floor_line.append(Tile("1"))

        # Place tiles
        if line != -1:
            spaces = line + 1 - len(player.pattern_lines[line])
            player.pattern_lines[line].extend(taken_tiles[:spaces])
            player.floor_line.extend(taken_tiles[spaces:])
        else:
            player.floor_line.extend(taken_tiles)

    def is_game_over(self) -> bool:
        """Check if the game is over.

        Returns:
            True if any player has completed a row
        """
        return any(
            all(cell is not None for cell in row)
            for player in self.players
            for row in player.wall
        )

    def end_game_scoring(self) -> None:
        """Calculate and apply end game scoring."""
        for player in self.players:
            rows, cols, colors = self.logic.calculate_end_game_bonus(player)
            player.score += rows + cols + colors

    def display_options(self) -> None:
        """Display available moves to the player."""
        print("\nAvailable factories:")
        for factory in self.factories:
            if factory.tiles:
                print(
                    f"{factory.name}: {' '.join(tile.color for tile in factory.tiles)}"
                )

        if self.center.tiles:
            print(f"Center: {' '.join(tile.color for tile in self.center.tiles)}")

    def get_user_source_choice(self) -> Source:
        """Get the player's choice of source.

        Returns:
            The chosen source
        """
        valid_factories = [
            factory.name[-1] for factory in self.factories if factory.tiles
        ]
        while True:
            if valid_factories:
                if self.is_center_valid_choice():
                    choice = input(
                        f"Choose a factory ({', '.join(valid_factories)}) or C for center: "
                    ).upper()
                    if choice == "C" and self.center:
                        return self.center
                    elif choice in valid_factories:
                        return self.factories[int(choice) - 1]
                else:
                    choice = input(f"Choose a factory ({', '.join(valid_factories)}): ")
                    if choice in valid_factories:
                        return self.factories[int(choice) - 1]
            else:
                print("Factories are empty, selecting from center.")
                return self.center
            print("Invalid choice. Please try again.")

    def is_center_valid_choice(self) -> bool:
        """Check if the center is a valid choice.

        Returns:
            True if the center has valid tiles to take (not just the first player token)
        """
        # Count tiles that are not the first player token
        valid_tiles = [tile for tile in self.center.tiles if tile.color != "1"]
        return len(valid_tiles) > 0

    def get_user_color_choice(self, source: Source) -> str:
        """Get the player's choice of color from a source.

        Args:
            source: The source to choose colors from

        Returns:
            The chosen color
        """
        available_colors = set(tile.color for tile in source.tiles if tile.color != "1")
        while True:
            color = input(f"Choose a color ({', '.join(available_colors)}): ").upper()
            if color in available_colors:
                return color
            print("Invalid color. Please try again.")

    def choose_pattern_line(self, valid_lines: List[int]) -> int:
        """Get the player's choice of pattern line.

        Args:
            valid_lines: List of valid line indices

        Returns:
            The chosen line index (-1 for floor line)
        """
        self.display.display_player_board(self.players[self.active_player])
        while True:
            line = input(
                f"Choose a pattern line ({', '.join([str(line + 1) for line in valid_lines])}), or F for floor line: "
            ).upper()
            if line == "F":
                return -1
            elif line.isdigit() and int(line) - 1 in valid_lines:
                return int(line) - 1
            print("Invalid choice. Please try again.")

    def end_round(self) -> None:
        """End the current round, moving tiles to walls and resetting factories."""
        for player in self.players:
            self.move_to_wall(player)
        self.reset_factories()

    def move_to_wall(self, player: Player) -> None:
        """Move completed pattern lines to the wall.

        Args:
            player: The player whose pattern lines to process
        """
        for i, line in enumerate(player.pattern_lines):
            if len(line) == i + 1:  # Line is complete
                color = line[0].color
                if self.mode == "pattern":
                    col = self.wall_pattern[i].index(color)
                    player.wall[i][col] = color
                    player.score += self.logic.score_tile(player, i, col)
                    self.discard.extend(line)
                else:
                    valid_cols = [
                        j
                        for j in range(5)
                        if player.wall[i][j] is None
                        and all(player.wall[k][j] != color for k in range(5))
                    ]
                    if valid_cols:
                        if self.verbose:
                            print(
                                f"Valid columns for {color} tile: {', '.join(map(str, [c+1 for c in valid_cols]))}"
                            )
                        while True:
                            try:
                                col = (
                                    int(
                                        input(
                                            f"Choose a column (1-5) for the {color} tile: "
                                        )
                                    )
                                    - 1
                                )
                                if col in valid_cols:
                                    break
                                print("Invalid column. Please try again.")
                            except ValueError:
                                print("Please enter a valid number.")
                        player.wall[i][col] = color
                        player.score += self.logic.score_tile(player, i, col)
                        self.discard.extend(line)
                    else:
                        if self.verbose:
                            print(
                                f"No valid columns for {color} tile. Moving to floor line."
                            )
                        player.floor_line.extend(line)
                player.pattern_lines[i] = []

        # Score floor line penalties
        points_lost = self.logic.calculate_floor_penalty(len(player.floor_line))
        player.score = max(0, player.score - points_lost)
        self.discard.extend(player.floor_line)
        player.floor_line = []

    def reset_factories(self) -> None:
        """Reset factories for the next round."""
        # Refill bag from discard if needed
        if len(self.bag) < len(self.factories) * 4:
            playable_tiles = [tile for tile in self.discard if tile.color != "1"]
            self.bag.extend(playable_tiles)
            self.discard = [tile for tile in self.discard if tile.color == "1"]
            random.shuffle(self.bag)

        # Fill factories
        for factory in self.factories:
            factory.tiles = [self.bag.pop() for _ in range(4) if self.bag]

        # Reset center with first player token
        self.center.tiles = [Tile("1")]
