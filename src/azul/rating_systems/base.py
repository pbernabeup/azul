"""Base class for rating systems."""

import json
from pathlib import Path

# Game outcome constants
WIN = 1
DRAW = 0
LOSS = -1


class BaseRatingSystem:
    """Base class for rating systems."""

    def __init__(
        self,
        ratings_file: str,
        results_file: str,
        reset: bool = False,
        save_results: bool = True,
    ):
        """Initialize the rating system.

        Args:
            ratings_file: Path to save/load ratings
            results_file: Path to save detailed matchup results
            reset: Whether to reset all ratings to default
            save_results: Whether to save results after each update
        """
        self.ratings_file = Path(ratings_file)
        self.results_file = Path(results_file)
        self.save_results_enabled = save_results
        self.ratings = {}
        self.matchups = {}

        # Load existing data if not resetting
        if not reset and self.ratings_file.exists():
            self._load_ratings()
        if not reset and self.results_file.exists() and save_results:
            self._load_results()

    def _load_ratings(self) -> None:
        """Load ratings from file if it exists."""
        try:
            with open(self.ratings_file) as f:
                self.ratings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.ratings = {}

    def _load_results(self) -> None:
        """Load matchup results from file if it exists."""
        try:
            with open(self.results_file) as f:
                self.matchups = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.matchups = {}

    def save_ratings(self) -> None:
        """Save current ratings to file. Always saves regardless of save_results setting."""
        self.ratings_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.ratings_file, "w") as f:
            json.dump(self.ratings, f, indent=2)

    def save_results(self) -> None:
        """Save matchup results to file. Only saves if save_results is enabled."""
        if not self.save_results_enabled:
            return

        self.results_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.results_file, "w") as f:
            json.dump(self.matchups, f, indent=2)

    def update_matchup_stats(self, first: str, second: str, score: int) -> None:
        """Update head-to-head statistics for a matchup.

        Args:
            first: Name of the first strategy
            second: Name of the second strategy
            score: Game outcome (WIN, DRAW, or LOSS) from first strategy's perspective
        """
        if not self.save_results_enabled:
            return

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
        else:  # DRAW
            self.matchups[first][second]["draws"] += 1

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

    def get_ratings_table(self) -> str:
        """Generate a formatted string of current ratings."""
        raise NotImplementedError("Subclasses must implement get_ratings_table")
