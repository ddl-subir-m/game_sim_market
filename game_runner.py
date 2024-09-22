import asyncio
import os
import time
from autogen import AssistantAgent, UserProxyAgent
from dotenv import load_dotenv
from entities import GameState, SharedMarket
from game_logic import process_action, process_cooperative_upgrade, update_game_state
from constants import GAME_RULES

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

# Configure the LLMs
openai_agent1_config = {
    "model": "gpt-3.5-turbo",
    "api_key": openai_api_key,
}

# Configure the LLMs
openai_agent2_config = {
    "model": "gpt-4o-mini",
    "api_key": openai_api_key,
}


def run_game(player1_config: dict, player2_config: dict):
    shared_market = SharedMarket()
    
    # Create AutoGen agents for players
    player1_agent = AssistantAgent(name="Player1", llm_config={"config_list": [openai_agent1_config]}, **player1_config)
    player2_agent = AssistantAgent(name="Player2", llm_config={"config_list": [openai_agent2_config]}, **player2_config)
    
    # Create UserProxyAgents to interact with the AssistantAgents
    player1_proxy = UserProxyAgent(name="Player1Proxy",human_input_mode="NEVER")
    player2_proxy = UserProxyAgent(name="Player2Proxy",human_input_mode="NEVER")
    
    player1_state = GameState()
    player2_state = GameState()

    # Prepare game rules and instructions
    game_instructions = f"""
    You are playing a farming game. Here are the rules:
    {GAME_RULES}
    
    Available actions:
    1. Plant(crop_type, plot_number)
    2. Harvest(plot_number)
    3. Buy(item, quantity)
    4. Sell(item, quantity)
    5. Rest()
    
    Make decisions to maximize your score. Your score is calculated as:
    Total money + Value of harvested crops
    """

    for day in range(1, GAME_RULES["total_days"] + 1):
        # Process actions for both players
        for player, agent, proxy, state in [
            ("Player 1", player1_agent, player1_proxy, player1_state),
            ("Player 2", player2_agent, player2_proxy, player2_state)
        ]:
            # Prepare game state information
            game_info = {
                "day": day,
                "player_state": state.dict(),
                "shared_market": shared_market.dict()
            }
            
            # Ask agent for decision
            message = f"""
            {game_instructions}
            
            Current game state:
            {game_info}
            
            Make a decision for {player} based on this game state. 
            Respond with a single action in the format: ActionName(parameter1, parameter2)
            """
            
            chat_result = proxy.initiate_chat(agent, message=message, max_turns=1)
            action = parse_action(chat_result)
            
            # Process the action
            if action['name'] == "BuyCooperative":
                result = process_cooperative_upgrade(player1_state, player2_state, shared_market, action)
            else:
                result = process_action(state, shared_market, action)
            print(f"Day {day}, {player}: {action} - {result}")
        
        # Process end of day
        update_game_state(player1_state)
        update_game_state(player2_state)
        
        time.sleep(0.1)  # Small delay to prevent blocking

    # Game over, determine winner
    player1_score = player1_state.money + sum(player1_state.harvested_crops.values())
    player2_score = player2_state.money + sum(player2_state.harvested_crops.values())
    
    if player1_score > player2_score:
        winner = "Player 1"
    elif player2_score > player1_score:
        winner = "Player 2"
    else:
        winner = "Tie"
    
    print(f"Game Over! {winner} wins!")
    print(f"Player 1 score: {player1_score}")
    print(f"Player 2 score: {player2_score}")

def parse_action(chat_result):
    action_str = chat_result.summary.strip()
    
    # Split the action string into action name and parameters
    action_parts = action_str.split('(')
    action_name = action_parts[0]
    
    # Remove the closing parenthesis and split parameters
    parameters = action_parts[1].rstrip(')').split(',')
    parameters = [param.strip() for param in parameters]
    
    # Create an Action object or dictionary
    action = {
        'name': action_name,
        'parameters': parameters
    }
    
    return action

