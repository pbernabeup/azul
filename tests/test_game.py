"""Tests for the Azul game implementation."""

import pytest

from src.azul.game import AzulGame


@pytest.fixture
def game() -> AzulGame:
    """Create a new game instance for testing."""
    return AzulGame(2)


def test_game_initialization(game: AzulGame) -> None:
    """Test that a new game is properly initialized."""
    assert game is not None
    assert len(game.players) == 2
    assert len(game.factories) == 5  # 2 players * 2 + 1
    assert len(game.center.tiles) == 1  # First player token
