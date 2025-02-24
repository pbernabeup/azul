"""Glicko2 rating system for evaluating CPU strategies."""

import json
import math
from dataclasses import dataclass
from typing import List, Tuple

from .base import DRAW, LOSS, WIN, BaseRatingSystem

# Constants
MU = 1500  # Default rating
PHI = 350  # Default rating deviation (RD)
SIGMA = 0.06  # Default volatility
TAU = 0.5  # System constant for volatility weight (reduced from 1.0)
EPSILON = 0.000001  # Convergence tolerance
MAX_ITERATIONS = 100  # Maximum iterations for volatility calculation
SCALE = 173.7178  # Glicko2 scale factor (400/ln(10))
CONVERGENCE_TOLERANCE = 0.000001  # Convergence tolerance for iterative calculations
PI_SQUARED = math.pi * math.pi


@dataclass
class Glicko2Player:
    """Represents a player in the Glicko2 rating system.

    Attributes:
        name: Name of the player/strategy
        mu: Rating value
        phi: Rating deviation (RD)
        sigma: Rating volatility
        games_played: Total number of games played
        wins: Number of games won
        losses: Number of games lost
        draws: Number of games drawn
    """

    name: str
    mu: float = MU
    phi: float = PHI
    sigma: float = SIGMA
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


class Glicko2System(BaseRatingSystem):
    """Glicko2 rating system for evaluating CPU strategies."""

    def __init__(
        self,
        ratings_file: str = "analysis/glicko2_ratings.json",
        results_file: str = "analysis/results.json",
        reset: bool = False,
        tau: float = TAU,
        default_rating: float = MU,
        default_rd: float = PHI,
        default_vol: float = SIGMA,
        save_results: bool = True,
    ):
        """Initialize the Glicko2 rating system.

        Args:
            ratings_file: Path to save/load ratings
            results_file: Path to save detailed matchup results
            reset: Whether to reset all ratings to default
            tau: System constant, smaller values change ratings more slowly
            default_rating: Default rating for new players
            default_rd: Default rating deviation for new players
            default_vol: Default volatility for new players
            save_results: Whether to save results after each update
        """
        super().__init__(ratings_file, results_file, reset, save_results)
        self.tau = tau
        self.default_rating = default_rating
        self.default_rd = default_rd
        self.default_vol = default_vol

        # Initialize ratings if resetting or no file exists
        if reset or not self.ratings_file.exists():
            self.ratings = {}
        elif not reset:
            self._load_ratings()

    def _load_ratings(self) -> None:
        """Load ratings from file if it exists."""
        try:
            with open(self.ratings_file) as f:
                self.ratings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.ratings = {}

    def save_ratings(self) -> None:
        """Save current ratings to file."""
        self.ratings_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.ratings_file, "w") as f:
            json.dump(self.ratings, f, indent=2)

    def get_player(self, name: str) -> Glicko2Player:
        """Get a player by name, creating a new one if it doesn't exist."""
        if name not in self.players:
            self.players[name] = Glicko2Player(name)
        return self.players[name]

    def scale_down(
        self, rating: Glicko2Player, ratio: float = 173.7178
    ) -> Glicko2Player:
        """Convert rating to Glicko2 scale."""
        mu = (rating.mu - self.default_rating) / ratio
        phi = rating.phi / ratio
        return Glicko2Player(rating.name, mu, phi, rating.sigma)

    def scale_up(self, rating: Glicko2Player, ratio: float = 173.7178) -> Glicko2Player:
        """Convert rating back to original scale."""
        mu = rating.mu * ratio + self.default_rating
        phi = rating.phi * ratio
        return Glicko2Player(rating.name, mu, phi, rating.sigma)

    def reduce_impact(self, rating: Glicko2Player) -> float:
        """Calculate g(RD) to reduce impact of games based on RD."""
        return 1.0 / math.sqrt(1 + (3 * rating.phi**2) / (math.pi**2))

    def expect_score(
        self, rating: Glicko2Player, other: Glicko2Player, impact: float
    ) -> float:
        """Calculate expected score."""
        return 1.0 / (1 + math.exp(-impact * (rating.mu - other.mu)))

    def determine_sigma(
        self, rating: Glicko2Player, difference: float, variance: float
    ) -> float:
        """Determine new sigma (volatility) value with iteration limit."""
        phi = rating.phi
        difference_squared = difference**2
        alpha = math.log(rating.sigma**2)

        def f(x: float) -> float:
            tmp = phi**2 + variance + math.exp(x)
            a = math.exp(x) * (difference_squared - tmp) / (2 * tmp**2)
            b = (x - alpha) / (self.tau**2)
            return a - b

        # Initial values
        a = alpha
        if difference_squared > phi**2 + variance:
            b = math.log(difference_squared - phi**2 - variance)
        else:
            k = 1
            while f(alpha - k * math.sqrt(self.tau**2)) < 0:
                k += 1
                if k > MAX_ITERATIONS:  # Prevent infinite loop
                    return math.exp(alpha / 2)
            b = alpha - k * math.sqrt(self.tau**2)

        f_a, f_b = f(a), f(b)
        iterations = 0

        # Iterate until convergence or max iterations
        while abs(b - a) > EPSILON and iterations < MAX_ITERATIONS:
            iterations += 1
            c = a + (a - b) * f_a / (f_b - f_a)
            f_c = f(c)

            if f_c * f_b < 0:
                a, f_a = b, f_b
            else:
                f_a /= 2
            b, f_b = c, f_c

        return math.exp(a / 2)

    def rate(
        self, rating: Glicko2Player, series: List[Tuple[float, Glicko2Player]]
    ) -> Glicko2Player:
        """Update rating based on game results."""
        # Convert to Glicko2 scale
        rating = self.scale_down(rating)

        if not series:
            # If no games played, only increase uncertainty
            phi_star = math.sqrt(rating.phi**2 + rating.sigma**2)
            return self.scale_up(
                Glicko2Player(rating.name, rating.mu, phi_star, rating.sigma)
            )

        # Calculate variance and difference
        variance_inv = 0
        difference = 0
        for actual_score, other_rating in series:
            other_rating = self.scale_down(other_rating)
            impact = self.reduce_impact(other_rating)
            expected_score = self.expect_score(rating, other_rating, impact)
            variance_inv += impact**2 * expected_score * (1 - expected_score)
            difference += impact * (actual_score - expected_score)

        difference /= variance_inv
        variance = 1.0 / variance_inv

        # Update volatility
        sigma = self.determine_sigma(rating, difference, variance)

        # Update rating deviation
        phi_star = math.sqrt(rating.phi**2 + sigma**2)
        phi = 1.0 / math.sqrt(1 / phi_star**2 + 1 / variance)

        # Update rating
        mu = rating.mu + phi**2 * (difference / variance)

        # Convert back to original scale
        return self.scale_up(Glicko2Player(rating.name, mu, phi, sigma))

    def update_ratings(self, first: str, second: str, score: int) -> None:
        """Update ratings based on game outcome.

        Args:
            first: Name of the first strategy
            second: Name of the second strategy
            score: Game outcome (WIN, DRAW, or LOSS) from first strategy's perspective
        """
        # Get or create ratings
        if first not in self.ratings:
            self.ratings[first] = {
                "rating": self.default_rating,
                "rd": self.default_rd,
                "vol": self.default_vol,
                "games": 0,
            }

        if second not in self.ratings:
            self.ratings[second] = {
                "rating": self.default_rating,
                "rd": self.default_rd,
                "vol": self.default_vol,
                "games": 0,
            }

        rating1 = self.ratings[first]
        rating2 = self.ratings[second]

        # Convert game outcome to Glicko2 score
        if score == WIN:
            glicko_score = 1.0
        elif score == LOSS:
            glicko_score = 0.0
        else:  # DRAW
            glicko_score = 0.5

        # Update ratings
        new_r1, new_rd1, new_vol1 = self._compute_new_rating(
            rating1["rating"],
            rating1["rd"],
            rating1["vol"],
            (rating2["rating"], rating2["rd"], glicko_score),
        )
        new_r2, new_rd2, new_vol2 = self._compute_new_rating(
            rating2["rating"],
            rating2["rd"],
            rating2["vol"],
            (rating1["rating"], rating1["rd"], 1.0 - glicko_score),
        )

        # Store updated ratings
        rating1.update(
            {
                "rating": new_r1,
                "rd": new_rd1,
                "vol": new_vol1,
                "games": rating1["games"] + 1,
            }
        )
        rating2.update(
            {
                "rating": new_r2,
                "rd": new_rd2,
                "vol": new_vol2,
                "games": rating2["games"] + 1,
            }
        )

        # Update matchup statistics and save
        self.update_matchup_stats(first, second, score)
        if self.save_results_enabled:
            self.save_results()
        self.save_ratings()

    def update_matchup_stats(self, player1: str, player2: str, score: float) -> None:
        """Update head-to-head statistics for a matchup."""
        if player1 not in self.matchups:
            self.matchups[player1] = {}
        if player2 not in self.matchups:
            self.matchups[player2] = {}
        if player2 not in self.matchups[player1]:
            self.matchups[player1][player2] = {"wins": 0, "losses": 0, "draws": 0}
        if player1 not in self.matchups[player2]:
            self.matchups[player2][player1] = {"wins": 0, "losses": 0, "draws": 0}

        if score == WIN:
            self.matchups[player1][player2]["wins"] += 1
            self.matchups[player2][player1]["losses"] += 1
        elif score == LOSS:
            self.matchups[player1][player2]["losses"] += 1
            self.matchups[player2][player1]["wins"] += 1
        elif score == DRAW:
            self.matchups[player1][player2]["draws"] += 1
            self.matchups[player2][player1]["draws"] += 1

    def _load_results(self) -> None:
        """Load matchup results from the JSON file."""
        if not self.results_file.exists():
            return

        with open(self.results_file) as f:
            self.matchups = json.load(f)

    def save_results(self) -> None:
        """Save matchup results to the JSON file."""
        self.results_file.parent.mkdir(exist_ok=True)
        with open(self.results_file, "w") as f:
            json.dump(self.matchups, f, indent=4)

    def get_ratings_table(self) -> str:
        """Generate a formatted string of current ratings."""
        if not self.ratings:
            return "No ratings available."

        # Sort strategies by conservative rating estimate
        sorted_strategies = sorted(
            self.ratings.items(),
            key=lambda x: x[1]["rating"] - 2 * x[1]["rd"],
            reverse=True,
        )

        # Build table
        lines = []
        lines.append(
            f"{'Strategy':<15} {'Rating':<10} {'RD':<10} {'Vol':<10} {'Games':<10}"
        )
        lines.append("-" * 55)

        for strategy, data in sorted_strategies:
            rating_str = f"{data['rating']:.1f}"
            rd_str = f"±{data['rd']:.1f}"
            vol_str = f"{data['vol']:.3f}"
            games_str = str(data["games"])
            lines.append(
                f"{strategy:<15} {rating_str:<10} {rd_str:<10} {vol_str:<10} {games_str:<10}"
            )

        return "\n".join(lines)

    def get_matchup_table(self) -> str:
        """Get a formatted string of matchup statistics."""
        if not self.matchups:
            return "No matchup data available."

        strategies = sorted(self.matchups.keys())
        table = "Head-to-Head Results:\n"

        # Header
        table += f"{'Strategy':<12}"
        for strat in strategies:
            table += f"{strat[:8]:>12}"
        table += "\n" + "-" * (12 + 12 * len(strategies)) + "\n"

        # Data rows
        for strat1 in strategies:
            table += f"{strat1:<12}"
            for strat2 in strategies:
                if strat1 == strat2:
                    table += f"{'---':>12}"
                else:
                    stats = self.matchups[strat1].get(
                        strat2, {"wins": 0, "losses": 0, "draws": 0}
                    )
                    total = stats["wins"] + stats["losses"] + stats["draws"]
                    win_rate = (
                        (stats["wins"] + 0.5 * stats["draws"]) / total * 100
                        if total > 0
                        else 0
                    )
                    table += f"{win_rate:>11.1f}%"
            table += "\n"

        return table

    def _g(self, rd: float) -> float:
        """Calculate g(RD) function."""
        return 1.0 / (1 + 3 * rd * rd / (math.pi * math.pi))

    def _E(self, rating: float, opponent_rating: float, opponent_rd: float) -> float:
        """Calculate E function (expected score)."""
        return 1.0 / (
            1 + math.exp(-self._g(opponent_rd) * (rating - opponent_rating) / 400.0)
        )

    def _f(
        self, x: float, delta: float, phi: float, v: float, a: float, tau_squared: float
    ) -> float:
        """Calculate helper value for volatility computation.

        Internal helper function used as part of the Glicko-2 rating system's
        volatility calculation algorithm.
        """
        exp_x = math.exp(x)
        tmp = phi * phi + v + exp_x
        return (exp_x * (delta * delta - tmp)) / (2 * tmp * tmp) - (x - a) / tau_squared

    def _compute_new_rating(
        self,
        rating: float,
        rd: float,
        vol: float,
        opponent_data: Tuple[float, float, float],
    ) -> Tuple[float, float, float]:
        """Compute new rating values using the Glicko2 algorithm.

        Calculates updated rating, rating deviation, and volatility based on game outcome.

        Args:
            rating: Current rating
            rd: Current rating deviation
            vol: Current volatility
            opponent_data: Tuple of (opponent_rating, opponent_rd, score)

        Returns:
            Tuple of (new_rating, new_rd, new_vol)
        """
        # Scale ratings to Glicko2 scale
        mu = (rating - MU) / SCALE
        phi = rd / SCALE
        opponent_rating, opponent_rd, score = opponent_data
        opponent_mu = (opponent_rating - MU) / SCALE
        opponent_phi = opponent_rd / SCALE

        # Pre-compute common values
        g_term = 1.0 / math.sqrt(1 + 3 * opponent_phi * opponent_phi / PI_SQUARED)
        E_term = 1.0 / (1 + math.exp(-g_term * (mu - opponent_mu)))
        v_inv = g_term * g_term * E_term * (1 - E_term)

        if v_inv < EPSILON:  # Avoid division by zero
            return rating, rd, vol

        v = 1.0 / v_inv
        delta = v * g_term * (score - E_term)
        delta_squared = delta * delta
        phi_squared = phi * phi

        # Compute new volatility
        a = math.log(vol * vol)
        tau_squared = self.tau * self.tau

        if delta_squared > phi_squared + v:
            B = math.log(delta_squared - phi_squared - v)
        else:
            k = 1
            while True:
                B = a - k * self.tau
                if k > MAX_ITERATIONS or self._f(B, delta, phi, v, a, tau_squared) >= 0:
                    break
                k += 1

        # Binary search for new volatility
        A = a
        f_A = self._f(A, delta, phi, v, a, tau_squared)
        f_B = self._f(B, delta, phi, v, a, tau_squared)

        for _ in range(MAX_ITERATIONS):
            C = A + (A - B) * f_A / (f_B - f_A)
            f_C = self._f(C, delta, phi, v, a, tau_squared)

            if abs(B - A) < CONVERGENCE_TOLERANCE:
                break

            if f_C * f_B < 0:
                A, f_A = B, f_B
            else:
                f_A *= 0.5
            B, f_B = C, f_C

        # Update rating values
        new_vol = math.exp(A / 2)
        phi_star = math.sqrt(phi_squared + new_vol * new_vol)
        new_phi = 1.0 / math.sqrt(1.0 / (phi_star * phi_star) + 1.0 / v)
        new_mu = mu + new_phi * new_phi * g_term * (score - E_term)

        # Scale back to original scale
        return (
            new_mu * SCALE + MU,  # new rating
            new_phi * SCALE,  # new RD
            new_vol,  # new volatility
        )
