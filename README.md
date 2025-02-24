# Azul Game Implementation

A Python implementation of the Azul board game, featuring both human and AI players with multiple strategy levels.

## Features

- Complete implementation of Azul game rules
- Support for 2-5 players (human and/or AI)
- Four AI difficulty levels with different strategies:
  - Dummy: Takes first available valid move
  - Greedy: Maximizes immediate tile placement
  - Smart: Prioritizes adjacent placements and minimizes whitespace
  - Strategic: Balances diagonal moves, adjacency, and tile efficiency
  - Minmax: Uses minmax algorithm with opponent modeling
- Two game modes: pattern and free placement
- Command-line interface with detailed game state display
- Comprehensive AI performance analysis tools
- Multiple rating systems for strategy evaluation:
  - ELO with dynamic K-factor
  - Glicko2 with rating deviation and volatility
  - TrueSkill with Gaussian skill estimation

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/azul.git
cd azul
```

2. Create a virtual environment and install dependencies:
```bash
uv sync
```

## Project Structure

```
azul/
├── src/
│   └── azul/
│       ├── models/
│       │   ├── __init__.py
│       │   ├── tile.py
│       │   ├── source.py
│       │   └── player.py
│       ├── rating_systems/
│       │   ├── __init__.py
│       │   ├── base.py        # Base class for rating systems
│       │   ├── elo.py         # ELO rating system
│       │   ├── glicko2.py     # Glicko2 rating system
│       │   └── trueskill.py   # TrueSkill rating system
│       ├── __init__.py
│       ├── game.py          # Main game implementation
│       ├── game_logic.py    # Game rules and scoring
│       ├── display.py       # CLI display functionality
│       ├── cpu.py          # AI strategies implementation
│       ├── main.py         # CLI entry point
│       └── analyze_results.py  # Results analysis script
├── tests/
│   ├── conftest.py
│   ├── test_game.py
│   ├── test_game_logic.py
│   └── test_ai.py
├── analysis/               # Generated analysis outputs
│   ├── elo_ratings.json
│   ├── glicko2_ratings.json
│   ├── trueskill_ratings.json
│   ├── results.json
│   ├── win_rates.png
│   └── strategy_summary.csv
├── pyproject.toml         # Project configuration
├── .pre-commit-config.yaml # Development tools config
├── README.md
└── LICENSE
```

## Usage

### Playing the Game

```python
from azul.game import AzulGame

# Create a new game with 2 players
game = AzulGame(num_players=2, mode='pattern', verbose=True)

# Start the game
game.play_game()
```

### Command Line Interface

The game can be played directly from the command line:

```bash
# Play an interactive game
uv run python -m src.azul.main [--players N] [--mode {pattern,free}] [--difficulty N]

# Run AI strategy simulations
uv run python -m src.azul.main --simulate [--games N]

# Run a rating tournament
uv run python -m src.azul.main --rating-system {elo,glicko2,trueskill} [options]
```

## Game Modes

- **Pattern Mode**: Tiles must be placed according to the predefined pattern
- **Free Mode**: Tiles can be placed freely, following basic placement rules

## AI Strategies

1. **Dummy (Level 1)**
   - Takes the first available valid move
   - Prefers higher pattern lines
   - Falls back to floor line when necessary

2. **Greedy (Level 2)**
   - Maximizes immediate tile placement
   - Tries to fill pattern lines efficiently
   - Minimizes overflow to floor line

3. **Smart (Level 3)**
   - Prioritizes moves adjacent to existing tiles
   - Minimizes whitespace in pattern lines
   - Balances tile count with placement efficiency

4. **Strategic (Level 4)**
   - Prioritizes diagonal moves in first round
   - Considers both horizontal and vertical adjacency
   - Advanced overflow handling and tile efficiency

5. **Minmax**
   - Uses minmax algorithm with opponent modeling
   - Evaluates game states considering wall patterns
   - Predicts opponent moves using their actual strategy

## Rating Systems

The project includes three rating systems for evaluating AI strategies:

### ELO Rating System
- Traditional chess rating system with dynamic K-factor
- Features:
  - Dynamic K-factor that decreases with games played
  - Configurable initial K-factor, minimum K-factor, and decrease rate
  - Ratings start at 1000
  - Best for head-to-head comparisons
  - Fast convergence to accurate ratings

### Glicko2 Rating System
- Modern rating system that tracks rating uncertainty
- Features:
  - Rating (μ), deviation (RD), and volatility (σ) tracking
  - Better handling of inactive players
  - Configurable system parameters (τ)
  - Ratings start at 1500
  - More accurate for modern competitive games
  - Self-adjusting based on uncertainty

### TrueSkill Rating System
- Microsoft's Bayesian rating system
- Features:
  - Gaussian skill estimation with uncertainty
  - Supports both individual and team ratings
  - Fast convergence with few games
  - Built-in draw probability modeling
  - Conservative initial estimates
  - Ideal for multiplayer games

### Common Features
All rating systems share:
- Persistent storage of ratings and matchup statistics
- Detailed head-to-head win rate tracking
- Pretty-printed rating tables
- Conservative rating estimates
- Reset capability for fresh tournaments
- Configurable file paths for ratings and results

### Usage Examples

```bash
# Run tournament with ELO ratings
uv run python -m src.azul.main --rating-system elo --games 1000 --reset \
    --initial-k 32 --min-k 10 --k-decrease 0.5

# Run tournament with Glicko2 ratings
uv run python -m src.azul.main --rating-system glicko2 --games 1000 --reset

# Run tournament with TrueSkill ratings
uv run python -m src.azul.main --rating-system trueskill --games 1000 --reset

# Test specific strategies
uv run python -m src.azul.main --rating-system {elo,glicko2,trueskill} \
    --test-strategies minmax strategic
```

Common options:
- `--games N`: Number of games per matchup (default: 1000)
- `--reset`: Start with fresh ratings
- `--test-strategies`: List of strategies to test
- `--ratings-file`: Custom path for ratings file
- `--results-file`: Custom path for results file

ELO-specific options:
- `--initial-k`: Starting K-factor value (default: 32.0)
- `--min-k`: Minimum K-factor value (default: 10.0)
- `--k-decrease`: K-factor decrease per match (default: 1.0)

## Development

This project uses several development tools:

- `pytest` for testing
- `black` for code formatting
- `mypy` for type checking
- `flake8` for linting (with docstring checks)
- `isort` for import sorting
- `pre-commit` for automated checks

To set up the development environment:

```bash
uv add --dev pytest black mypy isort flake8 pre-commit
uv run pre-commit install
```

## Testing

Run the tests with:

```bash
pytest
```

For coverage report:

```bash
pytest --cov=src/azul --cov-report=html
```

## Analysis Tools

The project includes tools for analyzing AI strategy performance:

- Win rate analysis between strategies
- Average score comparisons
- First/second player advantage analysis
- Performance visualization with heatmaps
- Elo, Glicko2 and TrueSkill rating tracking
- Head-to-head statistics

Analysis results are saved in the `analysis` directory.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run the tests and ensure they pass
5. Run pre-commit checks (`pre-commit run --all-files`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Acknowledgements

- Original Azul game design by Michael Kiesling
- Greedy, smart and strategic CPU strategies based on "Achieving the maximal score in Azul" by Sara Kooistra
- Glicko2 implementation adapted from Heungsub Lee's glicko2 library

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
