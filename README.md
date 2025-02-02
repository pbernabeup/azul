# Azul CLI

Welcome to Azul CLI, a command-line interface version of the popular board game Azul! This repo contains a fully playable implementation of Azul that you can enjoy right in your terminal.

## Game Overview

Azul is an abstract strategy board game where players compete to create the most beautiful mosaic tile pattern. Players take turns drafting colored tiles from suppliers and placing them on their player board. Points are scored based on how the tiles are placed to decorate the palace. The player with the most points at the end of the game wins.

## Features

- Play Azul against computer opponents or simulate CPU self-play
- Different CPU difficulty levels for challenging gameplay
- Customizable game settings (number of players, game mode...)
- Interactive and user-friendly CLI interface

## Installation

1. Make sure you have Python 3.x installed on your system.
2. Clone this repository:
   ```
   git clone https://github.com/pbernabeup/azul.git
   ```
3. Navigate to the project directory:
   ```
   cd azul
   ```
4. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

To start playing Azul CLI, run the following command:
```
python azul.py play
```

Follow the on-screen instructions to set up the game and begin playing. Use the provided commands to draft tiles, place them on your player board and complete your turn.

To simulate CPU self-play, run the following command:
```
python azul.py simulate
```

## Contributing

Contributions to Azul CLI are welcome! If you find any bugs, have suggestions for improvements, or want to add new features, please open an issue or submit a pull request. Make sure to follow the existing code style and include appropriate tests.

## Acknowledgements

- Azul game design by Michael Kiesling
- Greedy, smart and strategic CPU strategies based on "Achieving the maximal score in Azul" by Sara Kooistra

Enjoy playing Azul in your terminal!