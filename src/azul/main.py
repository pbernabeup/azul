#!/usr/bin/env python3
"""Entry point for the Azul game."""
import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

from tqdm import tqdm

# Add the src directory to the Python path if running as script
if __name__ == "__main__":
    src_dir = str(Path(__file__).resolve().parent.parent.parent)
    sys.path.insert(0, src_dir)

from src.azul.cpu import AzulCPU
from src.azul.game import AzulGame

STRATEGIES = ["dummy", "greedy", "smart", "strategic"]


def play_game(args: Optional[argparse.Namespace] = None) -> None:
    """Play an interactive game of Azul.

    Args:
        args: Optional command line arguments. If not provided, will prompt for input.
    """
    if args is None:
        # Interactive mode
        num_players = 0
        while num_players < 2 or num_players > 5:
            try:
                num_players = int(
                    input("Please introduce the number of players (2-5): ")
                )
            except ValueError:
                print("Please enter a valid number")

        mode = ""
        while mode not in ["pattern", "free"]:
            mode = input("Please select gamemode (pattern or free): ").lower()

        difficulty = 0
        while difficulty < 1 or difficulty > 4:
            try:
                difficulty = int(input("Please introduce the difficulty level (1-4): "))
            except ValueError:
                print("Please enter a valid number")
    else:
        # Command line mode
        num_players = args.players
        mode = args.mode
        difficulty = args.difficulty

    game = AzulGame(num_players, mode=mode)
    # First player is human, rest are AI
    game.ai = [None] + [
        AzulCPU(game, STRATEGIES[difficulty - 1]) for _ in range(num_players - 1)
    ]
    game.play_game()


def simulate_games(num_games: int = 100000) -> None:
    """Run AI simulations to test different strategies.

    Args:
        num_games: Number of games to simulate for each strategy pair
    """
    for first_strategy in STRATEGIES:
        for second_strategy in STRATEGIES:
            print(f"\nSimulating: {first_strategy} vs {second_strategy}")

            results = [0, 0, 0]  # wins, losses, ties
            total_scores = [0, 0]

            for _ in tqdm(range(num_games), desc="Games"):
                game = AzulGame(2, mode="pattern", verbose=False)
                game.ai = [
                    AzulCPU(game, first_strategy),
                    AzulCPU(game, second_strategy),
                ]
                players = game.play_game()

                total_scores[0] += players[0].score
                total_scores[1] += players[1].score

                if players[0].score > players[1].score:
                    results[0] += 1
                elif players[1].score > players[0].score:
                    results[1] += 1
                else:
                    results[2] += 1

            save_simulation_results(
                first_strategy, second_strategy, results, total_scores, num_games
            )


def save_simulation_results(
    first_strategy: str,
    second_strategy: str,
    results: List[int],
    total_scores: List[int],
    num_games: int,
) -> None:
    """Save simulation results to a JSON file.

    Args:
        first_strategy: Name of the first AI strategy
        second_strategy: Name of the second AI strategy
        results: List of [wins, losses, ties]
        total_scores: List of total scores for each player
        num_games: Number of games simulated
    """
    # Ensure analysis directory exists
    os.makedirs("analysis", exist_ok=True)
    results_file = "analysis/results.json"

    if os.path.exists(results_file):
        with open(results_file, "r") as f:
            all_data: Dict = json.load(f)
    else:
        all_data = {}

    if first_strategy not in all_data:
        all_data[first_strategy] = {}

    all_data[first_strategy][second_strategy] = {
        "wins": results[0],
        "losses": results[1],
        "ties": results[2],
        "avg_first": total_scores[0] / num_games,
        "avg_second": total_scores[1] / num_games,
    }

    with open(results_file, "w") as f:
        json.dump(all_data, f, indent=4)


def main() -> None:
    """Run the main entry point with command line argument parsing."""
    parser = argparse.ArgumentParser(description="Play or simulate Azul games")

    # Create subparsers for different modes
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Play command
    play_parser = subparsers.add_parser("play", help="Play an interactive game")
    play_parser.add_argument(
        "--players",
        type=int,
        default=None,
        choices=range(2, 6),
        help="Number of players (2-5)",
    )
    play_parser.add_argument(
        "--mode", choices=["pattern", "free"], default=None, help="Game mode"
    )
    play_parser.add_argument(
        "--difficulty",
        type=int,
        choices=range(1, 5),
        default=None,
        help="AI difficulty (1-4)",
    )

    # Simulate command
    sim_parser = subparsers.add_parser("simulate", help="Run AI strategy simulations")
    sim_parser.add_argument(
        "--games", type=int, default=100000, help="Number of games to simulate"
    )

    args = parser.parse_args()

    if args.command == "play":
        play_game(args if any(vars(args).values()) else None)
    elif args.command == "simulate":
        simulate_games(args.games)
    else:
        # No command specified, run interactive play mode
        play_game()


if __name__ == "__main__":
    main()
