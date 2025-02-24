"""Rating systems for evaluating CPU strategies."""

from .base import DRAW, LOSS, WIN, BaseRatingSystem
from .elo import EloSystem
from .glicko2 import Glicko2System
from .trueskill import TrueSkillSystem

__all__ = [
    "BaseRatingSystem",
    "EloSystem",
    "Glicko2System",
    "TrueSkillSystem",
    "WIN",
    "DRAW",
    "LOSS",
]
