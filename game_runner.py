import asyncio
import os
import time
from autogen import AssistantAgent, UserProxyAgent
from dotenv import load_dotenv
from entities import GameState, Plot, SharedMarket
from game_logic import process_action, process_cooperative_upgrade, process_day, update_game_state
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
    # "model": "gpt-3.5-turbo",
    "api_key": openai_api_key,
}

# Convert GameState objects to dictionaries
def game_state_to_dict(state):
    return {
        "money": state.money,
        "harvested_crops": state.harvested_crops,
        "energy": state.energy,
        "invalid_action_count": state.invalid_action_count,
        "action_log": state.action_log,
    }

async def run_game(player1_config: dict, player2_config: dict, stop_event: asyncio.Event):
    shared_market = SharedMarket()
    
    # Create AutoGen agents for players
    player1_agent = AssistantAgent(name="Player1", llm_config={"config_list": [openai_agent1_config]}, **player1_config)
    player2_agent = AssistantAgent(name="Player2", llm_config={"config_list": [openai_agent2_config]}, **player2_config)
    
    # Create UserProxyAgents to interact with the AssistantAgents
    player1_proxy = UserProxyAgent(name="Player1Proxy",human_input_mode="NEVER")
    player2_proxy = UserProxyAgent(name="Player2Proxy",human_input_mode="NEVER")
    
    player1_state = GameState(money=GAME_RULES["starting_money"], energy=GAME_RULES["max_energy"], plots=[Plot()])
    player2_state = GameState(money=GAME_RULES["starting_money"], energy=GAME_RULES["max_energy"], plots=[Plot()])

    # Prepare game rules and instructions
    game_instructions = f"""
    You are playing a farming game. Here are the rules:
    {GAME_RULES}
    
    Available actions:
    1. Plant(crop_name, plot_number)
    2. Harvest(plot_number)
    3. Buy(item_name, quantity)
    4. Sell(crop_name, quantity, market_type)
    5. Rest()
    6. Maintenance(type_of_maintenance, plot_number)
    7. BuyCooperative(upgrade_name)

    Make decisions to maximize your score. Your score is calculated as:
    Total money + Value of harvested crops

    Important rules to remember:
    - You can only harvest crops that have 100% grown. The growth time for each crop is specified in the rules above.
    - Consider the best course of action, thinking through your decision step by step.
    - You can only plant on plots that do not have a crop. If a plot already has a crop, you need to harvest it first before planting a new one.
    - Each plot is numbered, starting from 1. Make sure you're using the correct plot number in your actions.
    - Before harvesting or planting, check the state of your plots to ensure the action is valid.

    Examples:
    - Plant(Corn, 2) # To Plant Corn on plot 2 (only if plot 2 is vacant)
    - Harvest(1) # To Harvest from plot 1 (only if the crop on plot 1 is 100% grown)
    - Sell(Wheat, 10, local) # To Sell 10 Wheat in the local market
    - Rest() # Rest
    - Buy(Irrigation)  # To buy an individual upgrade
    - Buy(Plot)  # To buy a plot
    - Maintenance(water, 3) # To perform maintenance (water) on plot 3
    - BuyCooperative(CommunityCenter)  # To buy a cooperative upgrade

    Notes:
    - You start with one plot (numbered 1).
    - Plot numbers in commands start from 1.
    - For buying plots or upgrades, you can use Buy(item_name) or Buy(item_name, 1). The quantity is ignored for these purchases.
    - To buy cooperative upgrades, use the BuyCooperative action with the upgrade name.
    - The Rest action doesn't require parameters.
    - For actions with only one parameter, still use the format ActionName(parameter).
    - Maintenance improves soil quality of the specified plot.
    - Cooperative upgrades benefit both players and require coordination.
    - Always check your current game state before making a decision to ensure your action is valid.

    Your game state will be provided in this format:
    Day: [current day]
    Season: [current season]
    Weather: [current weather]
    Money: [your current money]
    Energy: [your current energy]
    Plots:
    [list of plot statuses]
    Harvested Crops: [your harvested crops]
    Upgrades: [your upgrades]
    Invalid Actions: [number of invalid actions]
    Action Log:
    [list of your recent actions and their results]

    Plot status will show if a plot is vacant or what crop is growing, including its growth percentage.
    The Action Log provides a history of your recent actions and their outcomes, which can help inform your decision-making.
    """
    game_log = []
    player1_action = ""
    player2_action = ""

    for day in range(1, GAME_RULES["total_days"] + 1):
        # Check if the game should be stopped
        if stop_event.is_set():
            print("Game stopped")
            return
        # Process end of previous day and start of new day
        if day > 1:
            process_day(player1_state, player2_state, shared_market)

        day_log = []
        # Process actions for both players
        for player, agent, proxy, state in [
            ("Player 1", player1_agent, player1_proxy, player1_state),
            ("Player 2", player2_agent, player2_proxy, player2_state)
        ]:
            # Prepare game state information
            game_info = {
                "Day": day,
                "Season": state.season,
                "Weather": state.weather,
                "Money": state.money,
                "Energy": state.energy,
                "Plots": chr(10).join(state.get_plot_status(GAME_RULES)),
                "Harvested Crops": state.harvested_crops,
                "Upgrades": state.upgrades,
                "Invalid Actions": state.invalid_action_count,
                "Action Log": chr(10).join(state.action_log[-GAME_RULES["action_log_display_count"]:])  # Show last action_log_display_count actions
            }
            
            # Ask agent for decision
            message = f"""
            {game_instructions}
            
            Current game state:
            {game_info}
            
            Make a decision for {player} based on this game state. 
            Respond with a single action in the format: ActionName(parameter1, parameter2)
            For actions with fewer than two parameters, use ActionName(parameter) or ActionName()
            """
            
            chat_result = await proxy.a_initiate_chat(agent, message=message, max_turns=1)
            action = parse_action(chat_result)
            if player == "Player 1":
                player1_action = {"name": action['name'], "parameters": action.get('parameters', [])}
            else:
                player2_action = {"name": action['name'], "parameters": action.get('parameters', [])}

            
            # Process the action
            if action['name'] == "BuyCooperative":
                result = process_cooperative_upgrade(player1_state, player2_state, shared_market, action)
            else:
                result = process_action(state, shared_market, action)
            day_log.append(f"Day {day}, {player}: {action['name']}({', '.join(map(str, action.get('parameters', [])))}): {result}")

            # Check if the game should stop after each player's action
            if stop_event.is_set():
                print("Game stopped during player actions")
                return
        
        game_log.extend(day_log)
        
        # Yield the current game state after each day
        yield {
            "day": day,
            "player1": player1_state,
            "player2": player2_state,
            "shared_market": shared_market,
            "game_log": game_log,
            "player1_action": player1_action,
            "player2_action": player2_action,
            "player1_state": game_state_to_dict(player1_state),
            "player2_state": game_state_to_dict(player2_state),
            "player1_action_log": player1_state.action_log,
            "player2_action_log": player2_state.action_log,
        }

        # Check if the game should stop after yielding the state
        if stop_event.is_set():
            print("Game stopped after yielding state")
            return
        
        await asyncio.sleep(0.2)  # Small delay to prevent blocking

    # Game over, determine winner
    def calculate_final_score(player_state):
        crop_value = sum(player_state.harvested_crops.values())
        player_state.money += crop_value  # Add crop value to player's money
        return player_state.money

    player1_score = calculate_final_score(player1_state)
    player2_score = calculate_final_score(player2_state)
    
    if player1_score > player2_score:
        winner = "Player 1"
    elif player2_score > player1_score:
        winner = "Player 2"
    else:
        winner = "Tie"
    

    # Yield final game result
    yield {
        "day": day,
        "game_over": True,
        "winner": winner,
        "player1_score": player1_score,
        "player2_score": player2_score,
        "player1_state": game_state_to_dict(player1_state),
        "player2_state": game_state_to_dict(player2_state)
    }


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

