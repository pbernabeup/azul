"""TrueSkill rating system for evaluating CPU strategies."""

import json
from pathlib import Path
from typing import Dict

from trueskill import Rating, rate_1vs1

from .base import DRAW, LOSS, WIN, BaseRatingSystem


class TrueSkillSystem(BaseRatingSystem):
    """TrueSkill rating system for evaluating CPU strategies."""

    def __init__(
        self,
        ratings_file: str = "analysis/trueskill_ratings.json",
        results_file: str = "analysis/results.json",
        reset: bool = False,
        save_results: bool = True,
    ):
        """Initialize the TrueSkill rating system.

        Args:
            ratings_file: Path to save/load ratings
            results_file: Path to save detailed matchup results
            reset: Whether to reset all ratings to default
            save_results: Whether to save results after each update
        """
        super().__init__(ratings_file, results_file, reset, save_results)
        self.ratings: Dict[str, Dict[str, float]] = {}
        self.matchups: Dict[str, Dict[str, Dict[str, int]]] = {}

        # Initialize ratings if resetting or no file exists
        if reset or not self.ratings_file.exists():
            self.ratings = {}
        elif not reset:
            self._load_ratings()

    def _load_ratings(self) -> None:
        """Load ratings from file if it exists."""
        try:
            with open(self.ratings_file) as f:
                data = json.load(f)
                # Convert stored values back to TrueSkill Rating objects
                self.ratings = {
                    name: {"rating": Rating(mu=stats["mu"], sigma=stats["sigma"])}
                    for name, stats in data.items()
                }
        except (FileNotFoundError, json.JSONDecodeError):
            self.ratings = {}

    def _load_results(self) -> None:
        """Load matchup results from file if it exists."""
        try:
            with open(self.results_file, "r") as f:
                self.matchups = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.matchups = {}

    def save_ratings(self) -> None:
        """Save current ratings to file."""
        self.ratings_file.parent.mkdir(parents=True, exist_ok=True)

        # Convert Rating objects to serializable format
        data = {
            name: {"mu": rating["rating"].mu, "sigma": rating["rating"].sigma}
            for name, rating in self.ratings.items()
        }

        with open(self.ratings_file, "w") as f:
            json.dump(data, f, indent=2)

    def save_results(self) -> None:
        """Save matchup results to file."""
        # Create directory if it doesn't exist
        Path(self.results_file).parent.mkdir(parents=True, exist_ok=True)

        with open(self.results_file, "w") as f:
            json.dump(self.matchups, f, indent=2)

    def _get_rating(self, strategy: str) -> Rating:
        """Get the TrueSkill rating for a strategy."""
        if strategy not in self.ratings:
            self.ratings[strategy] = {"rating": Rating()}
        return self.ratings[strategy]["rating"]

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

        # Update ratings based on outcome
        if score == WIN:
            new_r1, new_r2 = rate_1vs1(rating1, rating2)
        elif score == LOSS:
            new_r2, new_r1 = rate_1vs1(rating2, rating1)
        elif score == DRAW:
            new_r1, new_r2 = rate_1vs1(rating1, rating2, drawn=True)

        # Store updated ratings
        self.ratings[first]["rating"] = new_r1
        self.ratings[second]["rating"] = new_r2

        # Update matchup statistics
        self.update_matchup_stats(first, second, score)
        if self.save_results_enabled:
            self.save_ratings()
            self.save_results()

    def update_matchup_stats(self, first: str, second: str, score: int) -> None:
        """Update head-to-head statistics for a matchup.

        Args:
            first: Name of the first strategy
            second: Name of the second strategy
            score: Game outcome (WIN, DRAW, or LOSS) from first strategy's perspective
        """
        # Initialize matchup data if needed
        if first not in self.matchups:
            self.matchups[first] = {}
        if second not in self.matchups[first]:
            self.matchups[first][second] = {"wins": 0, "losses": 0, "draws": 0}

        # Update statistics based on outcome
        if score == WIN:
            self.matchups[first][second]["wins"] += 1
        elif score == LOSS:
            self.matchups[first][second]["losses"] += 1
        elif score == DRAW:
            self.matchups[first][second]["draws"] += 1

    def get_ratings_table(self) -> str:
        """Generate a formatted string of current ratings."""
        if not self.ratings:
            return "No ratings available."

        # Sort strategies by rating (mu - 3*sigma for conservative estimate)
        sorted_strategies = sorted(
            self.ratings.items(),
            key=lambda x: (x[1]["rating"].mu - 3 * x[1]["rating"].sigma),
            reverse=True,
        )

        # Build table
        lines = []
        lines.append(f"{'Strategy':<15} {'Rating':<10} {'Uncertainty':<10}")
        lines.append("-" * 35)

        for strategy, data in sorted_strategies:
            rating = data["rating"]
            rating_str = f"{rating.mu:.1f}"
            sigma_str = f"±{rating.sigma:.1f}"
            lines.append(f"{strategy:<15} {rating_str:<10} {sigma_str:<10}")

        return "\n".join(lines)

    def get_matchup_table(self) -> str:
        """Generate a formatted string of head-to-head statistics."""
        if not self.matchups:
            return "No matchup data available."

        # Get all unique strategies
        strategies = sorted(
            set(
                list(self.matchups.keys())
                + [s for m in self.matchups.values() for s in m.keys()]
            )
        )

        # Build table header
        lines = ["Head-to-Head Win Rates:"]
        header = "vs.".ljust(12)
        for strat in strategies:
            header += f"{strat[:8]:>8}"
        lines.append(header)
        lines.append("-" * (12 + 8 * len(strategies)))

        # Build table rows
        for strat1 in strategies:
            row = f"{strat1[:11]:<11} "
            for strat2 in strategies:
                if strat1 == strat2:
                    row += "    -   "
                    continue

                # Calculate win rate
                if strat1 in self.matchups and strat2 in self.matchups[strat1]:
                    stats = self.matchups[strat1][strat2]
                    total = stats["wins"] + stats["losses"] + stats["draws"]
                    if total > 0:
                        win_rate = (stats["wins"] + 0.5 * stats["draws"]) / total
                        row += f"{win_rate:>7.1%}"
                    else:
                        row += "    -   "
                else:
                    row += "    -   "
            lines.append(row)

        return "\n".join(lines)
