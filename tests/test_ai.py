"""Tests for the AI strategies."""

import pytest

from src.azul.cpu import AzulCPU
from src.azul.game import AzulGame
from src.azul.models import Source, Tile


@pytest.fixture
def game() -> AzulGame:
    """Create a test game."""
    return AzulGame(2, verbose=False)


@pytest.fixture
def ai(game: AzulGame) -> AzulCPU:
    """Create a test AI."""
    return AzulCPU(game, "dummy")


def test_dummy_strategy_chooses_valid_move(game: AzulGame, ai: AzulCPU) -> None:
    """Test that dummy strategy always makes valid moves."""
    game.setup_game()
    source, color, line = ai.dummy_algorithm()

    # Check source is valid
    assert source in (game.factories + [game.center])

    # Check color exists in source
    assert any(tile.color == color for tile in source.tiles)

    # Check line is valid or floor
    if line != -1:
        assert 0 <= line < 5
        player = game.players[game.active_player]
        valid_lines = game.logic.get_valid_lines(
            player, color, game.mode, game.wall_pattern
        )
        assert line in valid_lines


def test_greedy_strategy_maximizes_tiles(game: AzulGame, ai: AzulCPU) -> None:
    """Test that greedy strategy tries to place maximum tiles."""
    ai.algorithm = "greedy"
    game.setup_game()

    # Set up a situation where one move is clearly better
    game.factories[0].tiles = [Tile("R")] * 4
    game.factories[1].tiles = [Tile("B")] * 2

    source, color, line = ai.greedy_algorithm()

    # Should choose the factory with 4 tiles
    assert source == game.factories[0]
    assert color == "R"
    assert line == 3  # Will choose line 3 as it's a good balance of size and efficiency


def test_smart_strategy_prefers_adjacent(game: AzulGame, ai: AzulCPU) -> None:
    """Test that smart strategy prefers moves adjacent to existing tiles."""
    ai.algorithm = "smart"

    # Create game in free mode to avoid pattern restrictions
    game = AzulGame(2, mode="free", verbose=False)
    ai.game = game
    game.setup_game()

    # Set up a situation where one move connects to existing tiles
    player = game.players[game.active_player]

    # Place tiles to create a clear adjacency opportunity
    player.wall[2][2] = "R"  # Center tile
    player.wall[2][1] = "B"  # Left of R
    player.wall[2][3] = "W"  # Right of R
    player.wall[1][2] = "K"  # Above R

    # Clear all factories except two
    game.factories = [Source("Factory 1"), Source("Factory 2")]

    # Set up clear choice between adjacent and non-adjacent
    game.factories[0].tiles = [Tile("B")] * 2  # Adjacent option (matches existing B)
    game.factories[1].tiles = [Tile("Y")] * 2  # Non-adjacent option

    source, color, line = ai.smart_algorithm()

    # Should choose the move that connects to existing tiles
    assert color == "B"  # B is adjacent to existing tiles


def test_ai_handles_no_valid_moves(game: AzulGame, ai: AzulCPU) -> None:
    """Test that AI gracefully handles situations with no valid moves."""
    # Clear all factories and center
    game.factories = []
    game.center.tiles = []

    with pytest.raises(RuntimeError, match="No valid moves available"):
        ai.dummy_algorithm()


def test_ai_handles_full_lines(game: AzulGame, ai: AzulCPU) -> None:
    """Test that AI correctly handles full pattern lines."""
    game.setup_game()
    player = game.players[game.active_player]

    # Fill all pattern lines except one
    for i in range(4):
        player.pattern_lines[i] = [Tile("R")] * (i + 1)

    source, color, line = ai.dummy_algorithm()

    # Should only choose the empty line or floor
    assert line in (4, -1)


def test_ai_ignores_center_at_start_of_round(game: AzulGame, ai: AzulCPU) -> None:
    """Test that AI ignores center when it only has first player token."""
    game.setup_game()

    # Clear all factories except one
    game.factories = [Source("Factory 1")]
    game.factories[0].tiles = [Tile("R")] * 2

    # Center should only have first player token
    assert len(game.center.tiles) == 1
    assert game.center.tiles[0].color == "1"

    # Try each strategy
    for strategy in ["dummy", "greedy", "smart", "strategic"]:
        ai.algorithm = strategy
        source, color, _ = ai.choose_move()

        # Should choose from factory, not center
        assert source == game.factories[0]
        assert color == "R"


def test_ai_considers_center_mid_round(game: AzulGame, ai: AzulCPU) -> None:
    """Test that AI considers center equally when it has valid tiles."""
    game.setup_game()

    # Set up a situation where center has better move
    game.factories = [Source("Factory 1")]
    game.factories[0].tiles = [Tile("R")] * 2  # 2 red tiles
    game.center.tiles = [Tile("1")] + [Tile("B")] * 4  # First player + 4 blue tiles

    # Try each strategy except dummy (which takes first valid move)
    for strategy in ["greedy", "smart", "strategic"]:
        print(f"\nTesting {strategy} strategy:")
        ai.algorithm = strategy
        source, color, line = ai.choose_move()
        print(f"Chose source: {source.name}, color: {color}, line: {line}")
        print(f"Factory tiles: {[t.color for t in game.factories[0].tiles]}")
        print(f"Center tiles: {[t.color for t in game.center.tiles]}")

        # Should choose center's 4 blue tiles over factory's 2 red tiles
        assert source == game.center, f"{strategy} strategy chose factory over center"
        assert color == "B", f"{strategy} strategy chose {color} over B"


def test_greedy_prefers_more_tiles_regardless_of_source(
    game: AzulGame, ai: AzulCPU
) -> None:
    """Test that greedy strategy chooses most tiles regardless of source."""
    ai.algorithm = "greedy"
    game.setup_game()

    # Factory has 3 tiles, center has 4
    game.factories = [Source("Factory 1")]
    game.factories[0].tiles = [Tile("R")] * 3
    game.center.tiles = [Tile("1")] + [Tile("B")] * 4

    source, color, _ = ai.greedy_algorithm()
    assert source == game.center
    assert color == "B"

    # Now make factory have more tiles
    game.factories[0].tiles = [Tile("R")] * 5

    source, color, _ = ai.greedy_algorithm()
    assert source == game.factories[0]
    assert color == "R"


def test_smart_strategy_center_adjacency(game: AzulGame, ai: AzulCPU) -> None:
    """Test that smart strategy correctly evaluates adjacency from center tiles."""
    ai.algorithm = "smart"
    game = AzulGame(2, mode="free", verbose=False)
    ai.game = game
    game.setup_game()

    # Set up a wall with some tiles
    player = game.players[game.active_player]
    player.wall[2][2] = "R"  # Center tile

    # Factory has adjacent move, center has non-adjacent move
    game.factories = [Source("Factory 1")]
    game.factories[0].tiles = [Tile("W")] * 4  # Adjacent option (more tiles)
    game.center.tiles = [Tile("1")] + [Tile("Y")] * 2  # Non-adjacent option

    source, color, line = ai.smart_algorithm()

    # Should choose the factory with more tiles
    assert source == game.factories[0]
    assert color == "W"


def test_strategic_strategy_center_diagonal(game: AzulGame, ai: AzulCPU) -> None:
    """Test that strategic strategy correctly evaluates diagonal moves from center."""
    ai.algorithm = "strategic"
    game.setup_game()
    game.round_num = 1  # First round for diagonal priority

    # Factory has non-diagonal move, center has diagonal move
    game.factories = [Source("Factory 1")]
    game.factories[0].tiles = [Tile("W")] * 2  # Non-diagonal option
    game.center.tiles = [Tile("1")] + [
        Tile("R")
    ] * 2  # Diagonal option (R in position 0)

    # Set up wall pattern to ensure R is on diagonal
    game.wall_pattern = [
        ["R", "Y", "B", "K", "W"],  # R in position 0
        ["W", "R", "Y", "B", "K"],
        ["K", "W", "R", "Y", "B"],
        ["B", "K", "W", "R", "Y"],
        ["Y", "B", "K", "W", "R"],
    ]

    source, color, line = ai.strategic_algorithm()

    # Should choose the diagonal move from center
    assert source == game.center
    assert color == "R"
    # The strategic algorithm chooses line 1 as it balances diagonal priority with line size
    assert line == 1
