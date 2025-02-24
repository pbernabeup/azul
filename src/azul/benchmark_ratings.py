"""Benchmark different rating systems."""

import json
import time
from pathlib import Path
from typing import Dict, List, Tuple

from tqdm import tqdm

from .cpu import AzulCPU
from .game import AzulGame
from .rating_systems import DRAW, LOSS, WIN, EloSystem, Glicko2System, TrueSkillSystem

STRATEGIES = ["dummy", "greedy", "smart", "strategic", "minmax"]


def play_game(first_strategy: str, second_strategy: str) -> Tuple[AzulGame, int]:
    """Play a single game between two strategies.

    Args:
        first_strategy: Name of the first strategy
        second_strategy: Name of the second strategy

    Returns:
        Tuple of (game, score) where score is from first strategy's perspective
    """
    game = AzulGame(2, mode="pattern", verbose=False)
    game.ai = [
        AzulCPU(game, first_strategy),
        AzulCPU(game, second_strategy),
    ]
    players = game.play_game()

    # Determine game outcome from first player's perspective
    if players[0].score > players[1].score:
        score = WIN
    elif players[1].score > players[0].score:
        score = LOSS
    else:
        score = DRAW

    return game, score


def update_matchup_results(
    results: Dict,
    first: str,
    second: str,
    score: int,
) -> None:
    """Update matchup results dictionary with game outcome.

    Args:
        results: Dictionary containing matchup results
        first: Name of first strategy
        second: Name of second strategy
        score: Game outcome (WIN, DRAW, or LOSS) from first strategy's perspective
    """
    # Initialize dictionaries if needed
    for strat in (first, second):
        if strat not in results:
            results[strat] = {}

    for strat1, strat2 in ((first, second), (second, first)):
        if strat2 not in results[strat1]:
            results[strat1][strat2] = {"wins": 0, "losses": 0, "draws": 0}

    # Update statistics
    if score == WIN:
        results[first][second]["wins"] += 1
        results[second][first]["losses"] += 1
    elif score == LOSS:
        results[first][second]["losses"] += 1
        results[second][first]["wins"] += 1
    else:  # DRAW
        results[first][second]["draws"] += 1
        results[second][first]["draws"] += 1


def save_results(results: Dict, file_path: str) -> None:
    """Save results to file.

    Args:
        results: Dictionary containing results to save
        file_path: Path to save results to
    """
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w") as f:
        json.dump(results, f, indent=2)


def run_benchmark(num_games: int = 100, reset: bool = True) -> None:
    """Run a benchmark comparing all rating systems.

    Args:
        num_games: Number of games per matchup (will be doubled for both sides)
        reset: Whether to reset ratings
    """
    # Common results file for all systems
    results_file = "analysis/results.json"

    # Initialize rating systems - only ELO saves results, but all save ratings
    systems = {
        "ELO": EloSystem(
            ratings_file="analysis/elo_ratings.json",
            results_file=results_file,
            reset=reset,
            save_results=True,  # This system will save results
        ),
        "Glicko2": Glicko2System(
            ratings_file="analysis/glicko2_ratings.json",
            results_file=results_file,
            reset=reset,
            save_results=False,  # Don't save results from this system
        ),
        "TrueSkill": TrueSkillSystem(
            ratings_file="analysis/trueskill_ratings.json",
            results_file=results_file,
            reset=reset,
            save_results=False,  # Don't save results from this system
        ),
    }

    # Generate matchups
    matchups = [
        (first, second)
        for first in STRATEGIES
        for second in STRATEGIES
        if first != second
    ]

    total_games = num_games * len(matchups) * 2  # *2 because each plays both sides
    print(f"\nRunning {total_games} total games across {len(matchups)} matchups")
    print(f"Each matchup will play {num_games} games in each configuration")
    print(f"Testing all strategies: {', '.join(STRATEGIES)}\n")

    # Track timing statistics
    update_times: Dict[str, List[float]] = {name: [] for name in systems}
    games_played = 0

    with tqdm(total=total_games, desc="Total Progress") as pbar:
        for game_num in range(num_games):
            for first_strategy, second_strategy in matchups:
                # Play games in both configurations
                for strategies in [
                    (first_strategy, second_strategy),
                    (second_strategy, first_strategy),
                ]:
                    # Play the game
                    game, score = play_game(*strategies)
                    games_played += 1

                    # Update ratings for each system
                    for name, system in systems.items():
                        start_time = time.perf_counter()
                        system.update_ratings(strategies[0], strategies[1], score)
                        # Save ratings after every game
                        system.save_ratings()
                        end_time = time.perf_counter()
                        update_times[name].append(end_time - start_time)

                    pbar.update(1)

            # Print current ratings every 10% of games
            if game_num % (num_games // 10) == 0:
                print(f"\nRatings after {games_played} games:")
                for name, system in systems.items():
                    print(f"\n{name} Ratings:")
                    print(system.get_ratings_table())
                    print("\nHead-to-Head Win Rates:")
                    print(system.get_matchup_table())

    # Print final ratings and timing statistics
    print("\nFinal Ratings:")
    for name, system in systems.items():
        print(f"\n{name} Ratings:")
        print(system.get_ratings_table())
        print("\nHead-to-Head Win Rates:")
        print(system.get_matchup_table())

    # Print timing statistics
    print("\nTiming Statistics (seconds):")
    print(f"{'System':<12} {'Mean':>8} {'Min':>8} {'Max':>8} {'Total':>8}")
    print("-" * 46)
    for name, times in update_times.items():
        mean_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        total_time = sum(times)
        print(
            f"{name:<12} {mean_time:>8.6f} {min_time:>8.6f} {max_time:>8.6f} {total_time:>8.3f}"
        )


if __name__ == "__main__":
    run_benchmark()
