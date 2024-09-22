import asyncio
from game_runner import run_game
from constants import GAME_RULES

def main():
    player1_config = {
        "system_message": "You are an AI player in a farming game. Make decisions to maximize your score.",
        # Add other configuration options as needed
    }

    player2_config = {
        "system_message": "You are an AI player in a farming game. Make decisions to maximize your score.",
        # Add other configuration options as needed
    }

    run_game(player1_config, player2_config)

if __name__ == "__main__":
    main()