"""ELO rating system for evaluating CPU strategies."""

import json
from typing import Dict

from .base import DRAW, LOSS, WIN, BaseRatingSystem


class EloSystem(BaseRatingSystem):
    """ELO rating system for evaluating CPU strategies."""

    def __init__(
        self,
        ratings_file: str = "analysis/elo_ratings.json",
        results_file: str = "analysis/results.json",
        reset: bool = False,
        initial_k: float = 32.0,
        min_k: float = 10.0,
        k_decrease: float = 1.0,
        save_results: bool = True,
    ):
        """Initialize the ELO rating system.

        Args:
            ratings_file: Path to save/load ratings
            results_file: Path to save detailed matchup results
            reset: Whether to reset all ratings to default
            initial_k: The starting K-factor value
            min_k: The minimum K-factor value
            k_decrease: How much to decrease K-factor per match
            save_results: Whether to save results after each update
        """
        super().__init__(ratings_file, results_file, reset, save_results)
        self.initial_k = initial_k
        self.min_k = min_k
        self.k_decrease = k_decrease

        # Initialize ratings if resetting or no file exists
        if reset or not self.ratings_file.exists():
            self.ratings = {}

    def _load_ratings(self) -> None:
        """Load ratings from file if it exists."""
        try:
            with open(self.ratings_file) as f:
                data = json.load(f)
                self.ratings = {
                    name: {
                        "rating": stats["rating"],
                        "k_factor": stats["k_factor"],
                        "games": stats["games"],
                    }
                    for name, stats in data.items()
                }
        except (FileNotFoundError, json.JSONDecodeError):
            self.ratings = {}

    def save_ratings(self) -> None:
        """Save current ratings to file."""
        self.ratings_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.ratings_file, "w") as f:
            json.dump(self.ratings, f, indent=2)

    def _get_rating(self, strategy: str) -> Dict[str, float]:
        """Get or create rating data for a strategy."""
        if strategy not in self.ratings:
            self.ratings[strategy] = {
                "rating": 1500.0,
                "k_factor": self.initial_k,
                "games": 0,
            }
            # Save ratings when a new strategy is added
            if self.save_results_enabled:
                self.save_ratings()
        return self.ratings[strategy]

    def update_ratings(self, first: str, second: str, score: int) -> None:
        """Update ratings based on game outcome.

        Args:
            first: Name of the first strategy
            second: Name of the second strategy
            score: Game outcome (WIN, DRAW, or LOSS) from first strategy's perspective
        """
        # Get or create ratings
        rating1 = self._get_rating(first)
        rating2 = self._get_rating(second)

        # Calculate expected scores
        expected1 = 1 / (1 + 10 ** ((rating2["rating"] - rating1["rating"]) / 400))
        expected2 = 1 - expected1

        # Convert game outcome to score
        if score == WIN:
            actual1, actual2 = 1.0, 0.0
        elif score == LOSS:
            actual1, actual2 = 0.0, 1.0
        elif score == DRAW:
            actual1 = actual2 = 0.5

        # Update ratings
        rating1["rating"] += rating1["k_factor"] * (actual1 - expected1)
        rating2["rating"] += rating2["k_factor"] * (actual2 - expected2)

        # Update K-factors and game counts
        rating1["games"] += 1
        rating2["games"] += 1
        rating1["k_factor"] = max(
            self.min_k, self.initial_k - self.k_decrease * rating1["games"]
        )
        rating2["k_factor"] = max(
            self.min_k, self.initial_k - self.k_decrease * rating2["games"]
        )

        # Update matchup statistics and save
        self.update_matchup_stats(first, second, score)
        if self.save_results_enabled:
            self.save_results()  # Only save results if enabled
        self.save_ratings()  # Always save ratings

    def get_ratings_table(self) -> str:
        """Generate a formatted string of current ratings."""
        if not self.ratings:
            return "No ratings available."

        # Sort strategies by rating
        sorted_strategies = sorted(
            self.ratings.items(),
            key=lambda x: x[1]["rating"],
            reverse=True,
        )

        # Build table
        lines = []
        lines.append(f"{'Strategy':<15} {'Rating':<10} {'K-factor':<10} {'Games':<10}")
        lines.append("-" * 45)

        for strategy, data in sorted_strategies:
            rating_str = f"{data['rating']:.1f}"
            k_str = f"{data['k_factor']:.1f}"
            games_str = str(data["games"])
            lines.append(f"{strategy:<15} {rating_str:<10} {k_str:<10} {games_str:<10}")

        return "\n".join(lines)
