
import json
import os
import sys

from tqdm import tqdm

from AzulCPU import AzulCPU
from AzulGame import AzulGame

# Run the game
mode = sys.argv[1]
strategies = ["dummy", "greedy", "smart", "strategic"]

if mode == "play":
    num_players = 0
    while num_players < 2 or num_players > 5:
        num_players = int(input("Please introduce the number of players (2-5): "))
    
    mode = ''
    while mode not in ["pattern", "free"]:
        mode = input("Please select gamemode (pattern or free): ")
    
    difficulty = 0
    while difficulty < 1 or difficulty > 4:
        difficulty = int(input("Please introduce the difficulty level (1-4): "))

    game = AzulGame(num_players, mode=mode)
    game.ai = [None] + [AzulCPU(game, strategies[difficulty - 1]) for _ in range(num_players - 1)]
    game.play_game()

elif mode == "simulate":
    total_games = 100000

    for first_strategy in strategies:
        for second_strategy in strategies:
            print(first_strategy, second_strategy)

            results = [0, 0, 0]
            total_scores = [0, 0]

            for _ in tqdm(range(total_games)):
                game = AzulGame(2, mode='pattern', verbose=False)
                game.ai = [AzulCPU(game, first_strategy), AzulCPU(game, second_strategy)]
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

            if first_strategy not in data:
                data[first_strategy] = {}
            
            if second_strategy not in data[first_strategy]:
                data[first_strategy][second_strategy] = {}

            data[first_strategy][second_strategy] = {
                "wins": results[0],
                "losses": results[1],
                "ties": results[2],
                "avg_first": total_scores[0] / total_games,
                "avg_second": total_scores[1] / total_games,
            }

            with open("results.json", 'w') as f:
                json.dump(data, f, indent=4)
