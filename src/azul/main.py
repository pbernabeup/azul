#!/usr/bin/env python3
"""Entry point for the Azul game."""
import argparse
import sys
from pathlib import Path
from typing import List, Optional

from tqdm import tqdm

# Add the src directory to the Python path if running as script
if __name__ == "__main__":
    src_dir = str(Path(__file__).resolve().parent.parent.parent)
    sys.path.insert(0, src_dir)

from src.azul.cpu import AzulCPU
from src.azul.elo import EloSystem
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


def simulate_games(
    num_games: int = 100000,
    ratings_file: str = "analysis/elo_ratings.json",
    reset: bool = False,
    test_strategies: Optional[List[str]] = None,
) -> None:
    """Run AI simulations to test different strategies using ELO ratings.

    Args:
        num_games: Number of games to simulate for each strategy pair
        ratings_file: Path to the ratings file to load/save
        reset: Whether to reset all ratings to default
        test_strategies: Optional list of strategies to test. If provided, only these
            strategies will play against each other and existing ones.
    """
    elo = EloSystem(ratings_file=ratings_file)
    if reset:
        elo.players.clear()

    # Determine which strategies to test
    strategies_to_test = test_strategies if test_strategies else STRATEGIES
    all_strategies = sorted(set(list(elo.players.keys()) + strategies_to_test))

    # Generate matchups
    matchups = []
    for first_strategy in strategies_to_test:
        for second_strategy in all_strategies:
            if first_strategy >= second_strategy:  # Only play each matchup once
                continue
            matchups.append((first_strategy, second_strategy))

    if not matchups:
        print("No valid matchups found!")
        return

    total_games = num_games * len(matchups) * 2  # *2 because each plays both sides
    print(f"\nRunning {total_games} total games across {len(matchups)} matchups")
    print(f"Each matchup will play {num_games} games in each configuration")
    print(f"Testing strategies: {', '.join(strategies_to_test)}")
    if test_strategies:
        print(
            f"Against existing strategies: {', '.join(sorted(set(all_strategies) - set(strategies_to_test)))}\n"
        )
    print()

    with tqdm(total=total_games, desc="Total Progress") as pbar:
        # Run games in rounds, playing one game from each matchup
        for game_num in range(num_games):
            for first_strategy, second_strategy in matchups:
                # Play one game in first configuration
                game = AzulGame(2, mode="pattern", verbose=False)
                game.ai = [
                    AzulCPU(game, first_strategy),
                    AzulCPU(game, second_strategy),
                ]
                players = game.play_game()

                # Determine game outcome from first player's perspective
                if players[0].score > players[1].score:
                    score = 1.0  # First player won
                elif players[1].score > players[0].score:
                    score = 0.0  # First player lost
                else:
                    score = 0.5  # Draw

                # Update ELO ratings
                elo.update_ratings(first_strategy, second_strategy, score)
                pbar.update(1)

                # Play one game in reverse configuration
                game = AzulGame(2, mode="pattern", verbose=False)
                game.ai = [
                    AzulCPU(game, second_strategy),
                    AzulCPU(game, first_strategy),
                ]
                players = game.play_game()

                # Update ELO ratings for reverse matchup
                if players[0].score > players[1].score:
                    score = 0.0  # First strategy lost
                elif players[1].score > players[0].score:
                    score = 1.0  # First strategy won
                else:
                    score = 0.5  # Draw

                elo.update_ratings(first_strategy, second_strategy, score)
                pbar.update(1)

            # Print current ratings every 10% of games
            if game_num % (num_games // 10) == 0:
                print(f"\nRatings after {game_num * len(matchups) * 2} games:")
                print(elo.get_ratings_table())

    # Print final ratings
    print("\nFinal Ratings:")
    print(elo.get_ratings_table())


def run_elo_tournament(
    games_per_matchup: int = 1000,
    ratings_file: str = "analysis/elo_ratings.json",
    reset: bool = False,
    test_strategies: Optional[List[str]] = None,
) -> None:
    """Run a complete ELO rating tournament between all strategies.

    Args:
        games_per_matchup: Number of games to play for each strategy pair
        ratings_file: Path to the ratings file to load/save
        reset: Whether to reset all ratings to default
        test_strategies: Optional list of strategies to test
    """
    print("Starting ELO rating tournament...")
    print(
        f"Playing {games_per_matchup} games per matchup (doubled for playing both sides)"
    )

    simulate_games(
        num_games=games_per_matchup,
        ratings_file=ratings_file,
        reset=reset,
        test_strategies=test_strategies,
    )


def main() -> None:
    """Run the main entry point with command line argument parsing."""
    parser = argparse.ArgumentParser(description="Azul Game")
    parser.add_argument(
        "--players", type=int, default=2, help="Number of players (2-5)"
    )
    parser.add_argument(
        "--mode", type=str, default="pattern", help="Game mode (pattern or free)"
    )
    parser.add_argument("--difficulty", type=int, default=1, help="AI difficulty (1-4)")
    parser.add_argument(
        "--simulate", action="store_true", help="Run strategy simulations"
    )
    parser.add_argument("--elo", action="store_true", help="Run ELO rating tournament")
    parser.add_argument(
        "--games",
        type=int,
        default=1000,
        help="Number of games per matchup in tournaments",
    )
    parser.add_argument(
        "--ratings-file",
        type=str,
        default="analysis/elo_ratings.json",
        help="Path to the ratings file",
    )
    parser.add_argument(
        "--reset", action="store_true", help="Reset all ratings to default"
    )
    parser.add_argument(
        "--test-strategies",
        type=str,
        nargs="+",
        choices=STRATEGIES,
        help="Only test specific strategies",
    )

    args = parser.parse_args()

    if args.simulate:
        simulate_games(args.games)
    elif args.elo:
        run_elo_tournament(
            games_per_matchup=args.games,
            ratings_file=args.ratings_file,
            reset=args.reset,
            test_strategies=args.test_strategies,
        )
    else:
        play_game(args)


if __name__ == "__main__":
    main()
