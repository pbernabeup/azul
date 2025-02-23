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
- Two game modes: pattern and free placement
- Command-line interface with detailed game state display
- Comprehensive AI performance analysis tools

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
│       ├── __init__.py
│       ├── game.py          # Main game implementation
│       ├── game_logic.py    # Game rules and scoring
│       ├── display.py       # CLI display functionality
│       ├── cpu.py          # AI strategies implementation
│       ├── main.py         # CLI entry point
│       ├── analysis.py     # Analysis tools
│       └── analyze_results.py  # Results analysis script
├── tests/
│   ├── conftest.py
│   ├── test_game.py
│   ├── test_game_logic.py
│   └── test_ai.py
├── analysis/               # Generated analysis outputs
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
python -m src.azul.main play [--players N] [--mode {pattern,free}] [--difficulty N]

# Run AI strategy simulations
python -m src.azul.main simulate [--games N]

# Analyze simulation results
python -m src.azul.analyze_results [--output-dir DIR]
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

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
