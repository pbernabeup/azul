class AzulCPU:
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
        elif self.algorithm == 'strategic':
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

        if not best_move:
            best_move = self.find_least_negative()

        return best_move

    def smart_algorithm(self):
        best_move = None
        least_whitespace = float('inf')
        most_tiles = 0
        move_found = False
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
                                one_adjacent_move = False
                                most_tiles = 0

                            if not one_adjacent_move:
                                if self.has_adjacent(self.game, player, line_index, color):
                                    one_adjacent_move = True
                                    best_move = (source, color, line_index)
                                elif len(tiles) > most_tiles:
                                    best_move = (source, color, line_index)
                                    most_tiles = len(tiles)

        if not move_found:
            best_move = self.find_least_overflow(player)

        if not best_move:
            best_move = self.find_least_negative()

        return best_move

    def strategic_algorithm(self):
        best_move = None
        least_whitespace = float('inf')
        most_tiles = 0
        move_found = False
        diagonal_move = False
        one_adjacent_move = False
        two_adjacent_move = False
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
                                diagonal_move = two_adjacent_move = one_adjacent_move = False
                                most_tiles = 0

                            if not diagonal_move:
                                if self.game.round_num == 1:
                                    if self.is_move_in_diagonal(self.game, line_index, color):
                                        best_move = (source, color, line_index)
                                        diagonal_move = True
                                if not two_adjacent_move:
                                    adj_horiziontal, adj_vertical = self.check_adjacents(self.game, player, line_index, color)
                                    if adj_horiziontal and adj_vertical:
                                        best_move = (source, color, line_index)
                                        two_adjacent_move = True
                                if not two_adjacent_move and not one_adjacent_move:
                                    adj_horiziontal, adj_vertical = self.check_adjacents(self.game, player, line_index, color)
                                    if adj_horiziontal or adj_vertical:
                                        best_move = (source, color, line_index)
                                        one_adjacent_move = True
                                    elif len(tiles) > most_tiles:
                                        best_move = (source, color, line_index)
                                        most_tiles = len(tiles)

        if not move_found:
            best_move = self.find_least_overflow(player)

        if not best_move:
            best_move = self.find_least_negative()
        
        return best_move

    def find_least_overflow(self, player):
        best_move = None
        least = float('inf')

        for source in self.game.factories + [self.game.center]:
            for color in set(tile.color for tile in source.tiles if tile.color != '1'):
                tiles = [tile for tile in source.tiles if tile.color == color]
                for line_index in self.game.get_valid_lines(player, color):
                    spaces = line_index + 1 - len(player.pattern_lines[line_index])
                    tiles_too_many = abs(spaces - len(tiles))
                    if tiles_too_many < least:
                        least = tiles_too_many
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
                    return (False, False)

        horizontal = (col > 0 and player.wall[row][col-1]) or (col < 4 and player.wall[row][col+1])
        vertical = (row > 0 and player.wall[row-1][col]) or (row < 4 and player.wall[row+1][col])

        return (horizontal, vertical)

    def is_move_in_diagonal(self, game, row, color):
        return row == game.wall_pattern[row].index(color) if game.mode == 'pattern' else row == color
