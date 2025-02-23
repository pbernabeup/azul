"""Module containing display functionality for the Azul game."""

from typing import List

from .models import Player, Source


class Display:
    """Handles all display functionality for the Azul game."""

    @staticmethod
    def display_game_state(
        players: List[Player], factories: List[Source], center: Source
    ) -> None:
        """Display the current state of the game.

        Args:
            players: List of players in the game
            factories: List of factory displays
            center: The center display
        """
        print("\nGame State:")
        print("Factories:")
        for factory in factories:
            if factory.tiles:
                print(
                    f"{factory.name}: {' '.join(tile.color for tile in factory.tiles)}"
                )

        if center.tiles:
            print(f"\nCenter: {' '.join(tile.color for tile in center.tiles)}")

        print("\nPlayer Boards:")
        for player in players:
            Display.display_player_board(player)

    @staticmethod
    def display_player_board(player: Player) -> None:
        """Display a player's board state.

        Args:
            player: The player whose board to display
        """
        print(f"\n{player.name}'s Board (Score: {player.score})")

        print("Pattern Lines:")
        for i, line in enumerate(player.pattern_lines):
            spaces = i + 1
            print(
                f"{i+1}: {' '.join(tile.color for tile in line)}{' -' * (spaces - len(line))}"
            )

        print("\nWall:")
        for row in player.wall:
            print(" ".join(cell if cell else "-" for cell in row))

        if player.floor_line:
            print(f"\nFloor Line: {' '.join(tile.color for tile in player.floor_line)}")

    @staticmethod
    def display_turn_results(
        player: Player, source: Source, color: str, line: int
    ) -> None:
        """Display the results of a player's turn.

        Args:
            player: The player who took the turn
            source: The source they took tiles from
            color: The color they chose
            line: The line they placed tiles on (-1 for floor line)
        """
        print(f"\n{player.name} chose {source.name} and color {color}")

        if line != -1:
            print(f"{player.name} placed tiles on Pattern Line {line + 1}")
        else:
            print(f"{player.name} placed tiles on the Floor Line")
