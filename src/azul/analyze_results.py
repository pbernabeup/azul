#!/usr/bin/env python3
"""Script to analyze Azul simulation results."""
import argparse
from pathlib import Path

from .analysis import SimulationAnalyzer


def main() -> None:
    """Analyze simulation results and generate visualizations."""
    parser = argparse.ArgumentParser(description="Analyze Azul simulation results")
    parser.add_argument(
        "--results",
        type=str,
        default="analysis/results.json",
        help="Path to results JSON file",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="analysis",
        help="Directory to save analysis results",
    )

    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    # Initialize analyzer
    analyzer = SimulationAnalyzer(args.results)

    # Generate plots
    analyzer.plot_win_rates(str(output_dir / "win_rates.png"))
    analyzer.plot_average_scores(str(output_dir / "average_scores.png"))

    # Generate summary statistics
    summary = analyzer.get_strategy_summary()
    summary.to_csv(output_dir / "strategy_summary.csv")

    # Print summary to console
    print("\nStrategy Performance Summary:")
    print("=" * 80)
    print(summary.round(2))
    print("\nDetailed analysis saved to:", output_dir)


if __name__ == "__main__":
    main()
