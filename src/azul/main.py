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
from src.azul.game import AzulGame
from src.azul.rating_systems import (
    DRAW,
    LOSS,
    WIN,
    EloSystem,
    Glicko2System,
    TrueSkillSystem,
)

STRATEGIES = ["dummy", "greedy", "smart", "strategic", "minmax"]


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
    results_file: str = "analysis/results.json",
    reset: bool = False,
    test_strategies: Optional[List[str]] = None,
    rating_system: str = "elo",
    initial_k: float = 32.0,
    min_k: float = 10.0,
    k_decrease: float = 1.0,
) -> None:
    """Run AI simulations to test different strategies using ELO or Glicko2 ratings.

    Args:
        num_games: Number of games to simulate for each strategy pair
        ratings_file: Path to the ratings file to load/save
        results_file: Path to save detailed matchup results
        reset: Whether to reset all ratings to default
        test_strategies: Optional list of strategies to test. If provided, only these
            strategies will play against each other and existing ones.
        rating_system: Which rating system to use ('elo' or 'glicko2')
        initial_k: The starting K-factor value (ELO only)
        min_k: The minimum K-factor value (ELO only)
        k_decrease: How much to decrease K-factor per match (ELO only)
    """
    if rating_system == "elo":
        rating_engine = EloSystem(
            initial_k=initial_k,
            min_k=min_k,
            k_decrease=k_decrease,
            ratings_file=ratings_file,
            results_file=results_file,
            reset=reset,
        )
    elif rating_system == "glicko2":
        rating_engine = Glicko2System(
            ratings_file=ratings_file, results_file=results_file, reset=reset
        )
    else:  # trueskill
        rating_engine = TrueSkillSystem(
            ratings_file=ratings_file, results_file=results_file, reset=reset
        )

    # Determine which strategies to test
    strategies_to_test = test_strategies if test_strategies else STRATEGIES
    all_strategies = sorted(set(STRATEGIES))  # Use all defined strategies

    # Generate matchups
    matchups = []
    for first_strategy in strategies_to_test:
        for second_strategy in all_strategies:
            if first_strategy == second_strategy:  # Skip self-play
                continue
            matchups.append((first_strategy, second_strategy))

    if not matchups:
        print("No valid matchups found!")
        return

    total_games = num_games * len(matchups) * 2  # *2 because each plays both sides
    print(f"\nRunning {total_games} total games across {len(matchups)} matchups")
    print(f"Each matchup will play {num_games} games in each configuration")
    print(f"Using {rating_system.upper()} rating system")
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
                    score = WIN  # First player won
                elif players[1].score > players[0].score:
                    score = LOSS  # First player lost
                else:
                    score = DRAW  # Draw

                # Update ratings
                rating_engine.update_ratings(first_strategy, second_strategy, score)
                pbar.update(1)

                # Play one game in reverse configuration
                game = AzulGame(2, mode="pattern", verbose=False)
                game.ai = [
                    AzulCPU(game, second_strategy),
                    AzulCPU(game, first_strategy),
                ]
                players = game.play_game()

                # Update ratings for reverse matchup
                if players[0].score > players[1].score:
                    score = LOSS  # First strategy lost
                elif players[1].score > players[0].score:
                    score = WIN  # First strategy won
                else:
                    score = DRAW  # Draw

                rating_engine.update_ratings(first_strategy, second_strategy, score)
                pbar.update(1)

            # Print current ratings every 10% of games
            if game_num % (num_games // 10) == 0:
                print(f"\nRatings after {game_num * len(matchups) * 2} games:")
                print(rating_engine.get_ratings_table())
                print("\nHead-to-Head Win Rates:")
                print(rating_engine.get_matchup_table())

    # Print final ratings and matchup statistics
    print("\nFinal Ratings:")
    print(rating_engine.get_ratings_table())
    print("\nFinal Head-to-Head Win Rates:")
    print(rating_engine.get_matchup_table())


def run_elo_tournament(
    games_per_matchup: int = 1000,
    ratings_file: str = "analysis/elo_ratings.json",
    results_file: str = "analysis/results.json",
    reset: bool = False,
    test_strategies: Optional[List[str]] = None,
    rating_system: str = "elo",
    initial_k: float = 32.0,
    min_k: float = 10.0,
    k_decrease: float = 1.0,
) -> None:
    """Run a complete tournament between all strategies.

    Args:
        games_per_matchup: Number of games to play for each strategy pair
        ratings_file: Path to the ratings file to load/save
        results_file: Path to save detailed matchup results
        reset: Whether to reset all ratings to default
        test_strategies: Optional list of strategies to test
        rating_system: Which rating system to use ('elo' or 'glicko2')
        initial_k: The starting K-factor value (ELO only)
        min_k: The minimum K-factor value (ELO only)
        k_decrease: How much to decrease K-factor per match (ELO only)
    """
    print("Starting rating tournament...")
    print(
        f"Playing {games_per_matchup} games per matchup (doubled for playing both sides)"
    )
    print(f"Using {rating_system.upper()} rating system")
    if rating_system == "elo":
        print(
            f"K-factor: starts at {initial_k}, decreases by {k_decrease} per match until {min_k}"
        )

    simulate_games(
        num_games=games_per_matchup,
        ratings_file=ratings_file,
        results_file=results_file,
        reset=reset,
        test_strategies=test_strategies,
        rating_system=rating_system,
        initial_k=initial_k,
        min_k=min_k,
        k_decrease=k_decrease,
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
    parser.add_argument(
        "--rating-system",
        type=str,
        choices=["elo", "glicko2", "trueskill"],
        help="Run a rating tournament using the specified system",
    )
    parser.add_argument(
        "--games",
        type=int,
        default=1000,
        help="Number of games per matchup in tournaments",
    )
    parser.add_argument(
        "--initial-k",
        type=float,
        default=32.0,
        help="Initial K-factor value for ELO ratings",
    )
    parser.add_argument(
        "--min-k",
        type=float,
        default=10.0,
        help="Minimum K-factor value that it will decrease to",
    )
    parser.add_argument(
        "--k-decrease",
        type=float,
        default=1.0,
        help="How much to decrease K-factor per match",
    )
    parser.add_argument(
        "--ratings-file",
        type=str,
        default="analysis/elo_ratings.json",
        help="Path to the ratings file",
    )
    parser.add_argument(
        "--results-file",
        type=str,
        default="analysis/results.json",
        help="Path to save detailed matchup results",
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
    elif args.rating_system:
        # Adjust file paths based on rating system
        if args.rating_system == "glicko2":
            ratings_file = "analysis/glicko2_ratings.json"
            results_file = "analysis/glicko2_results.json"
        elif args.rating_system == "trueskill":
            ratings_file = "analysis/trueskill_ratings.json"
            results_file = "analysis/trueskill_results.json"
        else:
            ratings_file = args.ratings_file
            results_file = args.results_file

        run_elo_tournament(
            games_per_matchup=args.games,
            ratings_file=ratings_file,
            results_file=results_file,
            reset=args.reset,
            test_strategies=args.test_strategies,
            rating_system=args.rating_system,
            initial_k=args.initial_k,
            min_k=args.min_k,
            k_decrease=args.k_decrease,
        )
    else:
        play_game(args)


if __name__ == "__main__":
    main()
