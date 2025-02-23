"""ELO rating system for evaluating CPU strategies."""

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict


@dataclass
class EloPlayer:
    """Represents a player in the ELO rating system.

    Attributes:
        name: Name of the player/strategy
        rating: Current ELO rating
        games_played: Total number of games played
        wins: Number of games won
        losses: Number of games lost
        draws: Number of games drawn
    """

    name: str
    rating: float = 1500.0  # Starting ELO rating
    games_played: int = 0
    wins: int = 0
    losses: int = 0
    draws: int = 0

    @property
    def win_rate(self) -> float:
        """Calculate win rate as a percentage."""
        if self.games_played == 0:
            return 0.0
        return 100 * self.wins / self.games_played


class EloSystem:
    """Manages ELO ratings for CPU strategies."""

    def __init__(
        self, k_factor: float = 32.0, ratings_file: str = "analysis/elo_ratings.json"
    ):
        """Initialize the ELO rating system.

        Args:
            k_factor: The K-factor determines how much ratings change after each game
            ratings_file: Path to save/load ratings data
        """
        self.k_factor = k_factor
        self.ratings_file = Path(ratings_file)
        self.players: Dict[str, EloPlayer] = {}
        self._load_ratings()

    def _load_ratings(self) -> None:
        """Load ratings from the JSON file."""
        if not self.ratings_file.exists():
            return

        with open(self.ratings_file) as f:
            data = json.load(f)

        for name, player_data in data.items():
            self.players[name] = EloPlayer(
                name=name,
                rating=player_data["rating"],
                games_played=player_data["games_played"],
                wins=player_data["wins"],
                losses=player_data["losses"],
                draws=player_data["draws"],
            )

    def save_ratings(self) -> None:
        """Save current ratings to the JSON file."""
        self.ratings_file.parent.mkdir(exist_ok=True)

        data = {
            name: {
                "rating": player.rating,
                "games_played": player.games_played,
                "wins": player.wins,
                "losses": player.losses,
                "draws": player.draws,
            }
            for name, player in self.players.items()
        }

        with open(self.ratings_file, "w") as f:
            json.dump(data, f, indent=4)

    def get_player(self, name: str) -> EloPlayer:
        """Get a player by name, creating a new one if it doesn't exist.

        Args:
            name: Name of the player/strategy

        Returns:
            The EloPlayer object
        """
        if name not in self.players:
            self.players[name] = EloPlayer(name)
        return self.players[name]

    def expected_score(self, player_rating: float, opponent_rating: float) -> float:
        """Calculate expected score based on ELO formula.

        Args:
            player_rating: Rating of the player
            opponent_rating: Rating of the opponent

        Returns:
            Expected score between 0 and 1
        """
        return 1 / (1 + math.pow(10, (opponent_rating - player_rating) / 400))

    def update_ratings(self, player1: str, player2: str, score: float) -> None:
        """Update ratings after a game.

        Args:
            player1: Name of the first player
            player2: Name of the second player
            score: Actual score (1.0 for win, 0.5 for draw, 0.0 for loss) from player1's perspective
        """
        p1 = self.get_player(player1)
        p2 = self.get_player(player2)

        # Calculate expected scores
        expected_p1 = self.expected_score(p1.rating, p2.rating)
        expected_p2 = self.expected_score(p2.rating, p1.rating)

        # Update ratings
        p1.rating += self.k_factor * (score - expected_p1)
        p2.rating += self.k_factor * ((1 - score) - expected_p2)

        # Update statistics
        p1.games_played += 1
        p2.games_played += 1

        if score == 1.0:
            p1.wins += 1
            p2.losses += 1
        elif score == 0.0:
            p1.losses += 1
            p2.wins += 1
        else:  # Draw
            p1.draws += 1
            p2.draws += 1

        self.save_ratings()

    def get_ratings_table(self) -> str:
        """Get a formatted string of current ratings.

        Returns:
            Formatted ratings table as string
        """
        sorted_players = sorted(
            self.players.values(), key=lambda p: p.rating, reverse=True
        )

        table = "ELO Ratings:\n"
        table += f"{'Strategy':<15} {'Rating':>8} {'Games':>8} {'Win%':>8}\n"
        table += "-" * 41 + "\n"

        for player in sorted_players:
            table += (
                f"{player.name:<15} "
                f"{player.rating:>8.1f} "
                f"{player.games_played:>8d} "
                f"{player.win_rate:>7.1f}%\n"
            )

        return table
