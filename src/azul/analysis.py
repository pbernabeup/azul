"""Module for analyzing Azul game simulation results."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


@dataclass
class StrategyResult:
    """Results for a strategy matchup."""

    wins: int
    losses: int
    ties: int
    avg_first: float
    avg_second: float

    @property
    def total_games(self) -> int:
        """Total number of games played."""
        return self.wins + self.losses + self.ties

    @property
    def win_rate(self) -> float:
        """Win rate as a percentage."""
        return 100 * self.wins / self.total_games

    @property
    def loss_rate(self) -> float:
        """Loss rate as a percentage."""
        return 100 * self.losses / self.total_games

    @property
    def tie_rate(self) -> float:
        """Tie rate as a percentage."""
        return 100 * self.ties / self.total_games


class SimulationAnalyzer:
    """Analyzer for simulation results."""

    def __init__(self, results_file: str = "analysis/results.json"):
        """Initialize the analyzer.

        Args:
            results_file: Path to the results JSON file
        """
        self.results_file = Path(results_file)
        self.results: Dict[str, Dict[str, StrategyResult]] = {}
        self._load_results()

    def _load_results(self) -> None:
        """Load results from the JSON file."""
        if not self.results_file.exists():
            return

        with open(self.results_file) as f:
            data = json.load(f)

        for strat1 in data:
            self.results[strat1] = {}
            for strat2, result in data[strat1].items():
                self.results[strat1][strat2] = StrategyResult(**result)

    def get_win_rates(self) -> pd.DataFrame:
        """Get a DataFrame of win rates between strategies.

        Returns:
            DataFrame with win rates
        """
        strategies = sorted(self.results.keys())
        rates = []

        for strat1 in strategies:
            row = []
            for strat2 in strategies:
                if strat2 in self.results[strat1]:
                    row.append(self.results[strat1][strat2].win_rate)
                else:
                    row.append(np.nan)
            rates.append(row)

        return pd.DataFrame(rates, index=strategies, columns=strategies)

    def plot_win_rates(self, save_path: Optional[str] = None) -> None:
        """Plot a heatmap of win rates between strategies.

        Args:
            save_path: Optional path to save the plot
        """
        plt.figure(figsize=(10, 8))
        sns.heatmap(
            self.get_win_rates(),
            annot=True,
            fmt=".1f",
            cmap="RdYlGn",
            center=50,
            vmin=0,
            vmax=100,
            square=True,
        )
        plt.title("Strategy Win Rates (%)")
        if save_path:
            plt.savefig(save_path)
        plt.close()

    def get_average_scores(self) -> pd.DataFrame:
        """Get a DataFrame of average scores for each strategy.

        Returns:
            DataFrame with average scores
        """
        strategies = sorted(self.results.keys())
        first_scores = []
        second_scores = []

        for strat1 in strategies:
            first_row = []
            second_row = []
            for strat2 in strategies:
                if strat2 in self.results[strat1]:
                    result = self.results[strat1][strat2]
                    first_row.append(result.avg_first)
                    second_row.append(result.avg_second)
                else:
                    first_row.append(np.nan)
                    second_row.append(np.nan)
            first_scores.append(first_row)
            second_scores.append(second_row)

        first_df = pd.DataFrame(first_scores, index=strategies, columns=strategies)
        second_df = pd.DataFrame(second_scores, index=strategies, columns=strategies)
        return first_df, second_df

    def plot_average_scores(self, save_path: Optional[str] = None) -> None:
        """Plot heatmaps of average scores.

        Args:
            save_path: Optional path to save the plot
        """
        first_scores, second_scores = self.get_average_scores()

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))

        sns.heatmap(
            first_scores, annot=True, fmt=".1f", cmap="viridis", ax=ax1, square=True
        )
        ax1.set_title("Average Scores (Playing First)")

        sns.heatmap(
            second_scores, annot=True, fmt=".1f", cmap="viridis", ax=ax2, square=True
        )
        ax2.set_title("Average Scores (Playing Second)")

        if save_path:
            plt.savefig(save_path)
        plt.close()

    def get_strategy_summary(self) -> pd.DataFrame:
        """Get a summary of strategy performance.

        Returns:
            DataFrame with strategy statistics
        """
        strategies = sorted(self.results.keys())
        data = []

        for strat in strategies:
            total_games = 0
            total_wins = 0
            total_first_score = 0
            total_second_score = 0
            num_matchups = 0

            for opponent in strategies:
                if opponent in self.results[strat]:
                    result = self.results[strat][opponent]
                    total_games += result.total_games
                    total_wins += result.wins
                    total_first_score += result.avg_first
                    total_second_score += result.avg_second
                    num_matchups += 1

            if num_matchups > 0:
                data.append(
                    {
                        "Strategy": strat,
                        "Games Played": total_games,
                        "Win Rate (%)": 100 * total_wins / total_games,
                        "Avg Score (First)": total_first_score / num_matchups,
                        "Avg Score (Second)": total_second_score / num_matchups,
                    }
                )

        return pd.DataFrame(data).set_index("Strategy")
