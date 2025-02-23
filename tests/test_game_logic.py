"""Tests for the game logic module."""

import pytest

from src.azul.game_logic import GameLogic
from src.azul.models import Player, Tile


@pytest.fixture
def player() -> Player:
    """Create a test player."""
    return Player("Test Player")


def test_score_tile_no_connections(player: Player) -> None:
    """Test scoring a tile with no connections."""
    player.wall[2][2] = "R"
    assert GameLogic.score_tile(player, 2, 2) == 1


def test_score_tile_horizontal_connection(player: Player) -> None:
    """Test scoring a tile with horizontal connections."""
    player.wall[2][1] = "B"
    player.wall[2][2] = "R"
    player.wall[2][3] = "Y"
    assert GameLogic.score_tile(player, 2, 2) == 3


def test_score_tile_vertical_connection(player: Player) -> None:
    """Test scoring a tile with vertical connections."""
    player.wall[1][2] = "B"
    player.wall[2][2] = "R"
    player.wall[3][2] = "Y"
    assert GameLogic.score_tile(player, 2, 2) == 3


def test_score_tile_both_connections(player: Player) -> None:
    """Test scoring a tile with both horizontal and vertical connections."""
    player.wall[1][2] = "B"
    player.wall[2][1] = "W"
    player.wall[2][2] = "R"
    player.wall[2][3] = "Y"
    player.wall[3][2] = "K"
    assert GameLogic.score_tile(player, 2, 2) == 5


def test_calculate_floor_penalty() -> None:
    """Test floor line penalty calculation."""
    assert GameLogic.calculate_floor_penalty(0) == 0
    assert GameLogic.calculate_floor_penalty(1) == 1
    assert GameLogic.calculate_floor_penalty(3) == 4
    assert GameLogic.calculate_floor_penalty(7) == 14


def test_get_valid_lines_empty_pattern_mode(player: Player) -> None:
    """Test getting valid lines for an empty pattern line in pattern mode."""
    valid_lines = GameLogic.get_valid_lines(
        player,
        "R",
        "pattern",
        [
            ["B", "Y", "R", "K", "W"],
            ["W", "B", "Y", "R", "K"],
            ["K", "W", "B", "Y", "R"],
            ["R", "K", "W", "B", "Y"],
            ["Y", "R", "K", "W", "B"],
        ],
    )
    assert 2 in valid_lines  # Row where R appears in position 5


def test_get_valid_lines_partially_filled(player: Player) -> None:
    """Test getting valid lines for partially filled pattern lines."""
    player.pattern_lines[2] = [Tile("R"), Tile("R")]  # 2 tiles in 3-space line
    valid_lines = GameLogic.get_valid_lines(
        player,
        "R",
        "pattern",
        [
            ["B", "Y", "R", "K", "W"],
            ["W", "B", "Y", "R", "K"],
            ["K", "W", "B", "Y", "R"],
            ["R", "K", "W", "B", "Y"],
            ["Y", "R", "K", "W", "B"],
        ],
    )
    assert 2 in valid_lines


def test_get_valid_lines_full_line(player: Player) -> None:
    """Test getting valid lines when a line is full."""
    player.pattern_lines[2] = [Tile("R"), Tile("R"), Tile("R")]  # Full 3-space line
    valid_lines = GameLogic.get_valid_lines(
        player,
        "R",
        "pattern",
        [
            ["B", "Y", "R", "K", "W"],
            ["W", "B", "Y", "R", "K"],
            ["K", "W", "B", "Y", "R"],
            ["R", "K", "W", "B", "Y"],
            ["Y", "R", "K", "W", "B"],
        ],
    )
    assert 2 not in valid_lines


def test_calculate_end_game_bonus(player: Player) -> None:
    """Test end game bonus calculation."""
    # Complete one row
    player.wall[0] = ["R", "B", "Y", "K", "W"]

    # Complete one column
    for i in range(5):
        player.wall[i][0] = ["R", "B", "Y", "K", "W"][i]

    # Complete one color (R)
    for i in range(5):
        player.wall[i][i] = "R"

    rows, cols, colors = GameLogic.calculate_end_game_bonus(player)
    assert rows == 2  # 2 points per row
    assert cols == 7  # 7 points per column
    assert colors == 10  # 10 points per color
