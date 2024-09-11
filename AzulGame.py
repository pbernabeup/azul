import json
import os
import random
import sys
from tqdm import tqdm

class Tile:
    def __init__(self, color):
        self.color = color


class Source:
    def __init__(self, name):
        self.name = name
        self.tiles = []


class Player:
    def __init__(self, name, board_size=5):
        self.name = name
        self.pattern_lines = [[] for _ in range(board_size)]
        self.wall = [[None for _ in range(board_size)] for _ in range(board_size)]
        self.floor_line = []
        self.score = 0


class AzulAI:
    def __init__(self, game, algorithm):
        self.game = game
        self.algorithm = algorithm

    def choose_move(self):
        if self.algorithm == 'dummy':
            return self.dummy_algorithm()
        elif self.algorithm == 'greedy':
            return self.greedy_algorithm()
        elif self.algorithm == 'smart':
            return self.smart_algorithm()
        else:
            return self.strategic_algorithm()

    def dummy_algorithm(self):
        # Simple AI logic: choose the first available source and color, and the widest valid line
        for source in self.game.factories + [self.game.center]:
            chosen_color = next((tile.color for tile in source.tiles if tile.color != '1'), None)
            if chosen_color:
                player = self.game.players[self.game.active_player]
                valid_lines = self.game.get_valid_lines(player, chosen_color)
                chosen_line = max(valid_lines) if valid_lines else -1
                return source, chosen_color, chosen_line

    def greedy_algorithm(self):
        best_move = None
        largest = 0
        least = float('inf')
        player = self.game.players[self.game.active_player]

        for source in self.game.factories + [self.game.center]:
            for color in set(tile.color for tile in source.tiles if tile.color != '1'):
                tiles = [tile for tile in source.tiles if tile.color == color]
                for line_index in self.game.get_valid_lines(player, color):
                    spaces = line_index + 1 - len(player.pattern_lines[line_index])
                    if len(tiles) <= spaces:
                        if len(tiles) > largest:
                            largest = len(tiles)
                            best_move = (source, color, line_index)
                            least = 0
                    elif least != 0:
                        tiles_too_many = abs(spaces - len(tiles))
                        if tiles_too_many < least:
                            least = tiles_too_many
                            best_move = (source, color, line_index)

        # If no best_move found, choose the move that moves the least tiles to the floor line
        if not best_move:
            best_move = self.find_least_negative()

        return best_move

    def smart_algorithm(self):
        best_move = None
        least_whitespace = float('inf')
        most_tiles = 0
        move_found = False
        player = self.game.players[self.game.active_player]

        for source in self.game.factories + [self.game.center]:
            for color in set(tile.color for tile in source.tiles if tile.color != '1'):
                tiles = [tile for tile in source.tiles if tile.color == color]
                for line_index in self.game.get_valid_lines(player, color):
                    spaces = line_index + 1 - len(player.pattern_lines[line_index])
                    if len(tiles) <= spaces:
                        move_found = True
                        whitespace = spaces - len(tiles)
                        if whitespace <= least_whitespace:
                            if whitespace < least_whitespace:
                                least_whitespace = whitespace
                                best_move = None
                            if not best_move or self.has_adjacent(player, line_index, color):
                                best_move = (source, color, line_index)
                            elif len(tiles) > most_tiles:
                                best_move = (source, color, line_index)
                                most_tiles = len(tiles)

        if not move_found:
            best_move = self.find_least_overflow(player)

        return best_move if best_move else (None, None, None)

    def strategic_algorithm(self):
        best_move = None
        least_whitespace = float('inf')
        most_tiles = 0
        move_found = False
        diagonal_move = False
        two_adjacent_move = False
        one_adjacent_move = False
        player = self.game.players[self.game.active_player]

        for source in self.game.factories + [self.game.center]:
            for color in set(tile.color for tile in source.tiles if tile.color != '1'):
                tiles = [tile for tile in source.tiles if tile.color == color]
                for line_index in self.game.get_valid_lines(player, color):
                    spaces = line_index + 1 - len(player.pattern_lines[line_index])
                    if len(tiles) <= spaces:
                        move_found = True
                        whitespace = spaces - len(tiles)
                        if whitespace <= least_whitespace:
                            if whitespace < least_whitespace:
                                least_whitespace = whitespace
                                best_move = None
                                diagonal_move = two_adjacent_move = one_adjacent_move = False

                            if not diagonal_move and self.game.round_num == 1:
                                if self.is_move_in_diagonal(line_index, color):
                                    best_move = (source, color, line_index)
                                    diagonal_move = True
                            elif not two_adjacent_move:
                                adj = self.check_adjacents(player, line_index, color)
                                if adj['horizontal'] and adj['vertical']:
                                    best_move = (source, color, line_index)
                                    two_adjacent_move = True
                            elif not one_adjacent_move:
                                adj = self.check_adjacents(player, line_index, color)
                                if adj['horizontal'] or adj['vertical']:
                                    best_move = (source, color, line_index)
                                    one_adjacent_move = True
                            elif len(tiles) > most_tiles:
                                best_move = (source, color, line_index)
                                most_tiles = len(tiles)

        if not move_found:
            best_move = self.find_least_overflow(player)

        return best_move if best_move else (None, None, None)

    def find_least_overflow(self, player):
        best_move = None
        least_overflow = float('inf')

        for source in self.game.factories + [self.game.center]:
            for color in set(tile.color for tile in source.tiles if tile.color != '1'):
                tiles = [tile for tile in source.tiles if tile.color == color]
                for line_index, line in enumerate(player.pattern_lines):
                    if not line or line[0].color == color:
                        spaces = line_index + 1 - len(line)
                        overflow = max(0, len(tiles) - spaces)
                        if overflow < least_overflow:
                            least_overflow = overflow
                            best_move = (source, color, line_index)

        return best_move
    
    def find_least_negative(self):
        min_floor_tiles = float('inf')

        for source in self.game.factories + [self.game.center]:
            for color in set(tile.color for tile in source.tiles if tile.color != '1'):
                tiles = [tile for tile in source.tiles if tile.color == color]
                if len(tiles) < min_floor_tiles:
                    min_floor_tiles = len(tiles)
                    best_move = (source, color, -1)

        return best_move
    
    def has_adjacent(self, game, player, line_index, color):
        if game.mode == 'pattern':
            col = game.wall_pattern[line_index].index(color)
        else:
            col = next((j for j in range(5) if player.wall[line_index][j] is None and all(player.wall[k][j] != color for k in range(5))), None)
            if col is None:
                return False

        return self.check_adjacents(game, player, line_index, color, col)

    def check_adjacents(self, game, player, row, color, col=None):
        if col is None:
            if game.mode == 'pattern':
                col = game.wall_pattern[row].index(color)
            else:
                col = next((j for j in range(5) if player.wall[row][j] is None and all(player.wall[k][j] != color for k in range(5))), None)
                if col is None:
                    return {'horizontal': False, 'vertical': False}

        horizontal = (col > 0 and player.wall[row][col-1]) or (col < 4 and player.wall[row][col+1])
        vertical = (row > 0 and player.wall[row-1][col]) or (row < 4 and player.wall[row+1][col])

        return {'horizontal': horizontal, 'vertical': vertical}

    def is_move_in_diagonal(self, game, row, color):
        return row == game.wall_pattern[row].index(color) if game.mode == 'pattern' else row == color



class AzulGame:
    def __init__(self, num_players, mode='pattern', verbose=True):
        self.players = [Player(f"Player {i+1}") for i in range(num_players)]
        self.ai = [AzulAI(self, "dummy"), AzulAI(self, "dummy")]

        self.factories = [Source(f"Factory {i+1}") for i in range(num_players * 2 + 1)]
        self.center = Source("Center")
        self.bag = []
        self.discard = []
        
        self.round_num = 1
        self.active_player = 0
        self.first_player_token = 0
        self.mode = mode
        self.verbose = verbose

        self.colors = ['R', 'B', 'Y', 'K', 'W']  # Red, Blue, Yellow, blacK, White
        if mode == 'pattern':
            self.wall_pattern = [
                ['B', 'Y', 'R', 'K', 'W'],
                ['W', 'B', 'Y', 'R', 'K'],
                ['K', 'W', 'B', 'Y', 'R'],
                ['R', 'K', 'W', 'B', 'Y'],
                ['Y', 'R', 'K', 'W', 'B']
            ]
        else:
            self.wall_pattern = [[None for _ in range(5)] for _ in range(5)]

    def setup_game(self):
        self.bag = [Tile(color) for color in self.colors for _ in range(20)]
        random.shuffle(self.bag)
        for factory in self.factories:
            factory.tiles = [self.bag.pop() for _ in range(4) if self.bag]
        self.center.tiles = [Tile('1')]

    def play_round(self):
        self.active_player = self.first_player_token
        while any(factory.tiles for factory in self.factories) or self.is_center_valid_choice():
            player = self.players[self.active_player]
            if self.verbose:
                self.display_game_state()
            self.play_turn(player, is_ai=True)
            self.active_player = (self.active_player + 1) % len(self.players)

    def play_turn(self, player, is_ai=False):
        if self.verbose:
            print(f"\n{player.name}'s turn")
        
        if is_ai:
            chosen_source, chosen_color, chosen_line = self.ai[self.active_player].choose_move()
        else:
            chosen_source, chosen_color, chosen_line = self.user_input()

        # Take tiles
        taken_tiles = [tile for tile in chosen_source.tiles if tile.color == chosen_color]

        # Move tiles to center or update center
        if chosen_source != self.center:
            self.center.tiles.extend([tile for tile in chosen_source.tiles if tile.color != chosen_color])
            chosen_source.tiles.clear()
        else:
            self.center.tiles = [tile for tile in self.center.tiles if tile.color != chosen_color]

        # Handle first player token
        if chosen_source == self.center and any(tile.color == '1' for tile in self.center.tiles):
            self.center.tiles = [tile for tile in self.center.tiles if tile.color != '1']
            self.first_player_token = self.players.index(player)
            player.floor_line.append(Tile('1'))

        # Place tiles
        if chosen_line != -1:
            spaces = chosen_line + 1 - len(player.pattern_lines[chosen_line])
            player.pattern_lines[chosen_line].extend(taken_tiles[:spaces])
            player.floor_line.extend(taken_tiles[spaces:])
        else:
            player.floor_line.extend(taken_tiles)

        # Display turn results
        if self.verbose:
            self.display_turn_results(player, chosen_source, chosen_color, chosen_line)

    def user_input(self):
        # Display available options
        self.display_options()
        
        # Get user input for source choice
        chosen_source = self.get_user_source_choice()
        
        # Get user input for color choice
        chosen_color = self.get_user_color_choice(chosen_source)

        # Get user input for line choice
        player = self.players[self.active_player]
        valid_lines = self.get_valid_lines(player, chosen_color)
        chosen_line = self.choose_pattern_line(player, valid_lines)
        
        return chosen_source, chosen_color, chosen_line

    def display_options(self):
        print("\nAvailable factories:")
        for factory in self.factories:
            if factory.tiles:
                print(f"{factory.name}: {' '.join(tile.color for tile in factory.tiles)}")
        
        if self.center.tiles:
            print(f"Center: {' '.join(tile.color for tile in self.center.tiles)}")

    def get_user_source_choice(self):
        valid_factories = [factory for factory in self.factories if factory.tiles]
        while True:
            if valid_factories:
                if self.is_center_valid_choice():
                    choice = input(f"Choose a factory ({', '.join([factory.name[-1] for factory in valid_factories])}) or C for center: ").upper()
                    if choice == 'C' and self.center:
                        return self.center
                    elif choice in valid_factories:
                        return self.factories[int(choice) - 1]
                else:
                    choice = input(f"Choose a factory ({', '.join([factory.name[-1] for factory in valid_factories])}): ")
                    if choice in valid_factories:
                        return self.factories[int(choice) - 1]
            else:
                print("Factories are empty, selecting from center.")
                return self.center
            print("Invalid choice. Please try again.")
    
    def is_center_valid_choice(self):
        return len(self.center.tiles) > 2 or (len(self.center.tiles) == 1 and self.center.tiles[0].color != '1')

    def get_user_color_choice(self, chosen_source):
        available_colors = set(tile.color for tile in chosen_source.tiles if tile.color != '1')
        while True:
            color = input(f"Choose a color ({', '.join(available_colors)}): ").upper()
            if color in available_colors:
                return color
            print("Invalid color. Please try again.")

    def choose_pattern_line(self, player, valid_lines):
        self.display_player_board(player)
        while True:
            line = input(f"Choose a pattern line ({', '.join([str(line + 1) for line in valid_lines])}), or F for floor line: ").upper()
            if line == 'F':
                return -1
            elif line.isdigit() and int(line) - 1 in valid_lines:
                return int(line) - 1
            print("Invalid choice. Please try again.")

    def display_turn_results(self, player, chosen_source, chosen_color, chosen_line):
        print(f"{player.name} chose {chosen_source.name} and color {chosen_color}")
        
        if chosen_line != -1:
            print(f"{player.name} placed tiles on Pattern Line {chosen_line + 1}")
        else:
            print(f"{player.name} placed tiles on the Floor Line")

    def get_valid_lines(self, player, color):
        valid_lines = []
        for i, line in enumerate(player.pattern_lines):
            if len(line) == 0 or (line[0].color == color and len(line) < i + 1):
                if self.mode == 'pattern':
                    if color not in player.wall[i]:
                        valid_lines.append(i)
                else:
                    if color not in player.wall[i] and all(player.wall[i][j] != color for j in range(5)):
                        valid_lines.append(i)
        return valid_lines

    def end_round(self):
        for player in self.players:
            self.move_to_wall(player)
        self.reset_factories()

    def move_to_wall(self, player):
        for i, line in enumerate(player.pattern_lines):
            if len(line) == i + 1:
                color = line[0].color
                if self.mode == 'pattern':
                    col = self.wall_pattern[i].index(color)
                    player.wall[i][col] = color
                    self.score_tile(player, i, col)
                    self.discard.extend(line)
                else:
                    valid_cols = [j for j in range(5) if player.wall[i][j] is None and all(player.wall[k][j] != color for k in range(5))]
                    if valid_cols:
                        print(f"Valid columns for {color} tile: {', '.join(map(str, [c+1 for c in valid_cols]))}")
                        while True:
                            col = input(f"Choose a column (1-5) for the {color} tile: ")
                            if col.isdigit() and int(col) - 1 in valid_cols:
                                col = int(col) - 1
                                break
                            else:
                                print("Invalid column. Please try again.")
                        player.wall[i][col] = color
                        self.score_tile(player, i, col)
                        self.discard.extend(line)
                    else:
                        print(f"No valid columns for {color} tile. Moving to floor line.")
                        player.floor_line.extend(line)
                player.pattern_lines[i] = []

        floor_points = [1, 1, 2, 2, 2, 3, 3]
        points_lost = sum(floor_points[:len(player.floor_line)])
        player.score = max(0, player.score - points_lost)
        self.discard.extend(player.floor_line)
        player.floor_line = []

    def score_tile(self, player, row, col):
        score = 1
        horizontal_connection = False
        vertical_connection = False

        # Check horizontal
        left = right = col
        while left > 0 and player.wall[row][left-1]:
            left -= 1
            score += 1
            horizontal_connection = True
        while right < 4 and player.wall[row][right+1]:
            right += 1
            score += 1
            horizontal_connection = True
        
        # Check vertical
        up = down = row
        while up > 0 and player.wall[up-1][col]:
            up -= 1
            score += 1
            vertical_connection = True
        while down < 4 and player.wall[down+1][col]:
            down += 1
            score += 1
            vertical_connection = True
        
        # Add extra point if connected both horizontally and vertically
        if horizontal_connection and vertical_connection:
            score += 1

        player.score += score

    def reset_factories(self):
        if not self.bag:
            self.bag.extend([tile for tile in self.discard if tile.color != '1'])
            self.discard.clear()
            random.shuffle(self.bag)

        for factory in self.factories:
            factory.tiles = [self.bag.pop() for _ in range(4) if self.bag]

        self.center.tiles = [Tile('1')]

    def end_game_scoring(self):
        for player in self.players:
            player.score += 2 * sum(1 for row in player.wall if all(row))
            player.score += 7 * sum(1 for col in range(5) if all(player.wall[row][col] for row in range(5)))
            player.score += 10 * sum(1 for color in self.colors if all(player.wall[row][self.colors.index(color)] for row in range(5)))

    def display_game_state(self):
        print("\n" + "=" * 50)
        print("Game State:")
        print("=" * 50)

        print("\nFactories:")
        for factory in self.factories:
            if factory.tiles:
                print(f"{factory.name}: {' '.join(tile.color for tile in factory.tiles)}")
        
        if self.center.tiles:
            print(f"\nCenter: {' '.join(tile.color for tile in self.center.tiles)}")
        
        for player in self.players:
            self.display_player_board(player)

        print("\n" + "=" * 50)

    def display_player_board(self, player):
        print(f"\n{player.name}'s Board:")
        print("Pattern Lines:")
        for i, line in enumerate(player.pattern_lines):
            wall_row = ' '.join(tile if tile else '.' for tile in player.wall[i])
            pattern_line = ' '.join(tile.color for tile in line)
            empty_spaces = ' '.join('-' for _ in range(5 - (i + 1))) + ' ' if i < 4 else ''
            print(f"{i+1}: {(empty_spaces + pattern_line).ljust(9)} | {wall_row}")
        print(f"Floor Line: {' '.join(tile.color for tile in player.floor_line)}")
        print(f"Score: {player.score}")

    def play_game(self):
        self.setup_game()
        while not any(all(row) for player in self.players for row in player.wall):
            if self.verbose:
                print(f"\nRound {self.round_num}")
            self.play_round()
            self.end_round()
            if self.verbose:
                self.display_game_state()
            self.round_num += 1
        
        self.end_game_scoring()
        winner = max(self.players, key=lambda p: p.score)

        if self.verbose:
            print(f"\nThe game has ended!")
            for player in self.players:
                print(f"{player.name} final score: {player.score}")
            print(f"\nThe winner is {winner.name} with a score of {winner.score}!")

        return self.players

# Run the game
mode = sys.argv[1]
strategies = ["smart", "dummy"]

if mode == "play":
    game = AzulGame(2, mode='pattern')
    game.ai = [AzulAI(game, strategies[0]), AzulAI(game, strategies[1])]
    game.play_game()

elif mode == "simulate":
    total_games = 100000

    results = [0, 0, 0]
    total_scores = [0, 0]

    for _ in tqdm(range(total_games)):
        game = AzulGame(2, mode='pattern', verbose=False)
        game.ai = [AzulAI(game, strategies[0]), AzulAI(game, strategies[1])]
        players = game.play_game()

        total_scores[0] += players[0].score
        total_scores[1] += players[1].score

        if players[0].score > players[1].score:
            results[0] += 1
        elif players[1].score > players[0].score:
            results[1] += 1
        else:
            results[2] += 1
    
    if os.path.exists("results.json"):
        with open("results.json", 'r') as f:
            data = json.load(f)
    else:
        data = {}

    first, second = strategies

    if first not in data:
        data[first] = {}
    
    if second not in data[first]:
        data[first][second] = {}

    data[first][second] = {
        "wins": results[0],
        "losses": results[1],
        "ties": results[2],
        "avg_first": total_scores[0] / total_games,
        "avg_second": total_scores[1] / total_games,
    }

    with open("results.json", 'w') as f:
        json.dump(data, f, indent=4)
