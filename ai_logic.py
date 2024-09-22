import random
import logging
from entities import GameState, SharedMarket, Action
from constants import GAME_RULES

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def make_decision(state: GameState, shared_market: SharedMarket) -> Action:
    # This is a placeholder for more complex AI logic
    actions = [
        Action(type="plant", details={"crop_type": random.choice(list(GAME_RULES["crops"].keys())), "plot_index": random.randint(0, len(state.plots) - 1)}),
        Action(type="harvest", details={"plot_index": random.randint(0, len(state.plots) - 1)}),
        Action(type="maintenance", details={"maintenance_type": random.choice(["water", "weed", "fertilize"]), "plot_index": random.randint(0, len(state.plots) - 1)}),
        Action(type="sell", details={"crop_type": random.choice(list(GAME_RULES["crops"].keys())), "amount": random.randint(1, 10), "market_type": random.choice(["local", "global"])}),
        Action(type="buy", details={"item_type": random.choice(list(GAME_RULES["upgrades"].keys()) + ["plot"])}),
        Action(type="buy_cooperative_upgrade", details={"upgrade_type": random.choice(list(GAME_RULES["cooperative_upgrades"].keys()))})
    ]
    
    chosen_action = random.choice(actions)
    
    # Log the chosen action
    logger.info(f"AI chose action: {chosen_action.type} with details: {chosen_action.details}")
    
    return chosen_action