import random
from entities import GameState, Action, SharedMarket, Plot, Crop
from constants import GAME_RULES

def get_season(day: int) -> str:
    num_seasons = len(GAME_RULES["seasons"])
    return GAME_RULES["seasons"][((day - 1) // 30) % num_seasons]

def get_weather(season: str) -> str:
    return random.choices(GAME_RULES["weather_types"], GAME_RULES["weather_probabilities"][season])[0]

def update_market_trends(state: GameState):
    if state.day % GAME_RULES["market"]["trend_duration"] == 1:
        state.market_trends = {crop: random.uniform(0.8, 1.2) for crop in GAME_RULES["crops"]}

def plant_crop(state: GameState, action: Action) -> str:
    crop_type = action.details["crop_type"]
    plot_index = action.details["plot_index"] - 1  # Convert to 0-based index
    
    print(f"Attempting to plant {crop_type} on plot {plot_index + 1}. Total plots: {len(state.plots)}")
    
    if plot_index < 0 or plot_index >= len(state.plots):
        return f"Invalid plot number. You have {len(state.plots)} plot(s)."
    
    if state.plots[plot_index].crop is not None:
        return f"Plot {plot_index + 1} is not vacant"
    
    crop_cost = GAME_RULES["crops"][crop_type]["cost"]
    energy_cost = GAME_RULES["energy_cost"]["plant"][crop_type]
    
    if state.money < crop_cost or state.energy < energy_cost:
        return "Insufficient resources for planting"
    
    state.money -= crop_cost
    state.energy -= energy_cost
    state.plots[plot_index].crop = Crop(type=crop_type, planted_at=state.day)
    state.plots[plot_index].soil_quality -= GAME_RULES["soil_quality"]["depletion_rate"]
    
    return f"Planted {crop_type} in plot {plot_index}"

def harvest_crop(state: GameState, action: Action) -> str:
    plot_index = action.details["plot_index"] - 1  # Convert to 0-based index
    
    if plot_index < 0 or plot_index >= len(state.plots) or state.plots[plot_index].crop is None:
        return f"No crop to harvest in plot {plot_index + 1}"
    
    crop = state.plots[plot_index].crop
    crop_info = GAME_RULES["crops"][crop.type]
    energy_cost = GAME_RULES["energy_cost"]["harvest"][crop.type]
    
    if state.energy < energy_cost:
        return "Insufficient energy for harvesting"
    
    growth_time = crop_info["base_growth_time"]
    if (state.day - crop.planted_at) < growth_time:
        return "Crop not ready for harvest"
    
    state.energy -= energy_cost
    
    base_yield = crop_info["base_yield"]
    weather_factor = GAME_RULES["weather_effects"][state.weather]["yield"]
    soil_factor = 1 + (state.plots[plot_index].soil_quality - 1) * GAME_RULES["soil_quality"]["yield_factor"]
    total_yield = int(base_yield * weather_factor * soil_factor * crop.quality)
    
    state.harvested_crops[crop.type] = state.harvested_crops.get(crop.type, 0) + total_yield
    state.plots[plot_index].crop = None
    
    return f"Harvested {total_yield} {crop.type} from plot {plot_index + 1}"

def perform_maintenance(state: GameState, action: Action) -> str:
    maintenance_type = action.details["maintenance_type"]
    plot_index = action.details["plot_index"] - 1  # Convert to 0-based index
    
    if plot_index < 0 or plot_index >= len(state.plots):
        return f"Invalid plot number. You have {len(state.plots)} plot(s)."
    
    energy_cost = GAME_RULES["energy_cost"]["maintenance"][maintenance_type]
    
    if state.energy < energy_cost:
        return "Insufficient energy for maintenance"
    
    state.energy -= energy_cost
    state.plots[plot_index].soil_quality = min(1.0, state.plots[plot_index].soil_quality + GAME_RULES["soil_quality"]["maintenance_improvement"])
    
    if state.plots[plot_index].crop:
        state.plots[plot_index].crop.quality *= 1.1  # Improve crop quality
    
    return f"Performed {maintenance_type} maintenance on plot {plot_index + 1}"

def update_shared_market(market: SharedMarket, action: Action):
    if action.type == "sell":
        crop_type = action.details["crop_type"]
        amount = action.details["amount"]
        market.supply[crop_type] = market.supply.get(crop_type, 0) + amount
    elif action.type == "buy":
        crop_type = action.details["crop_type"]
        amount = action.details["amount"]
        market.demand[crop_type] = market.demand.get(crop_type, 0) + amount

def calculate_market_price(market: SharedMarket, crop_type: str, base_price: float) -> float:
    supply = market.supply.get(crop_type, 0)
    demand = market.demand.get(crop_type, 0)
    price_factor = 1 + (demand - supply) / 100  # Adjust this formula as needed
    return base_price * price_factor

def buy_cooperative_upgrade(state: GameState, other_state: GameState, action: Action) -> str:
    upgrade_type = action.details["upgrade_type"]
    if upgrade_type not in GAME_RULES["cooperative_upgrades"]:
        return "Invalid cooperative upgrade"
    
    upgrade_cost = GAME_RULES["cooperative_upgrades"][upgrade_type]["cost"]
    if state.money < upgrade_cost / 2 or other_state.money < upgrade_cost / 2:
        return "Insufficient funds for cooperative upgrade"
    
    state.money -= upgrade_cost / 2
    other_state.money -= upgrade_cost / 2
    state.upgrades.append(upgrade_type)
    other_state.upgrades.append(upgrade_type)
    
    return f"Purchased cooperative upgrade: {upgrade_type}"

def sell_crops(state: GameState, shared_market: SharedMarket, action: Action) -> str:
    crop_type = action.details["crop_type"]
    amount = action.details["amount"]
    market_type = action.details["market_type"]
    
    if crop_type not in state.harvested_crops or state.harvested_crops[crop_type] < amount:
        return "Insufficient crops for sale"
    
    energy_cost = GAME_RULES["energy_cost"]["trade"][market_type]
    
    if state.energy < energy_cost:
        return "Insufficient energy for trading"
    
    state.energy -= energy_cost
    
    base_price = GAME_RULES["crops"][crop_type]["base_price"]
    market_price = calculate_market_price(shared_market, crop_type, base_price)
    price_factor = GAME_RULES["market"]["local_price_factor"] if market_type == "local" else GAME_RULES["market"]["global_price_factor"]
    total_price = int(market_price * price_factor * amount)
    
    state.money += total_price
    state.harvested_crops[crop_type] -= amount
    
    # Update shared market
    update_shared_market(shared_market, action)
    
    return f"Sold {amount} {crop_type} for {total_price} money in the {market_type} market"

def buy_item(state: GameState, action: Action) -> str:
    item_type = action.details["item_type"]
    
    if item_type == "plot":
        current_plots = len(state.plots)
        cost = GAME_RULES["plot_purchase"]["base_cost"] * (GAME_RULES["plot_purchase"]["cost_increase_factor"] ** current_plots)
        
        if state.money < cost:
            return f"Insufficient funds to buy a new plot. Cost: {cost}, Available: {state.money}"
        
        state.money -= cost
        state.plots.append(Plot())
        return f"Purchased a new plot for {cost}. Total plots: {len(state.plots)}"
    
    elif item_type in GAME_RULES["upgrades"]:
        upgrade_cost = GAME_RULES["upgrades"][item_type]["cost"]
        
        if item_type in state.upgrades:
            return "Upgrade already purchased"
        
        if state.money < upgrade_cost:
            return "Insufficient money for upgrade"
        
        state.money -= upgrade_cost
        state.upgrades.append(item_type)
        
        return f"Purchased {item_type} upgrade"
    
    else:
        return f"Unknown item to buy: {item_type}"

def process_day(player1_state: GameState, player2_state: GameState, shared_market: SharedMarket):
    player1_state.day += 1
    player2_state.day += 1
    
    season = get_season(player1_state.day)
    player1_state.season = season
    player2_state.season = season
    
    weather = get_weather(season)
    player1_state.weather = weather
    player2_state.weather = weather
    
    player1_state.energy = min(player1_state.energy + GAME_RULES["energy_regen_per_day"], GAME_RULES["max_energy"])
    player2_state.energy = min(player2_state.energy + GAME_RULES["energy_regen_per_day"], GAME_RULES["max_energy"])
    
    update_market_trends(player1_state)
    update_market_trends(player2_state)
    
    # Apply upgrade effects and process crop growth for both players
    process_player_state(player1_state)
    process_player_state(player2_state)

def process_player_state(state: GameState):
    # Apply upgrade effects
    water_saving = 0
    weather_protection = 0
    yield_boost = 0
    energy_saving = 0
    
    for upgrade in state.upgrades:
        if upgrade in GAME_RULES["upgrades"]:
            upgrade_info = GAME_RULES["upgrades"][upgrade]
        elif upgrade in GAME_RULES["cooperative_upgrades"]:
            upgrade_info = GAME_RULES["cooperative_upgrades"][upgrade]
        else:
            continue

        if "water_saving" in upgrade_info:
            water_saving += upgrade_info["water_saving"]
        if "weather_protection" in upgrade_info:
            weather_protection += upgrade_info["weather_protection"]
        if "yield_boost" in upgrade_info:
            yield_boost += upgrade_info["yield_boost"]
        if "energy_saving" in upgrade_info:
            energy_saving += upgrade_info["energy_saving"]
    
    # Process crop growth
    for plot in state.plots:
        if plot.crop:
            growth_rate = GAME_RULES["weather_effects"][state.weather]["growth"]
            # Apply weather protection
            if weather_protection > 0:
                growth_rate = max(growth_rate, 1.0)  # Ensure growth rate is at least 1.0 (neutral)
            
            # Apply water saving (assuming it affects growth rate)
            growth_rate *= (1 + water_saving)
            
            new_growth = plot.crop.growth_progress + growth_rate / GAME_RULES["crops"][plot.crop.type]["base_growth_time"]
            plot.crop.growth_progress = min(1.0, new_growth)  # Cap growth at 100%
            
            # Apply yield boost to crop quality
            plot.crop.quality *= (1 + yield_boost)

            # Apply daily soil depletion
            plot.soil_quality = max(0, plot.soil_quality - GAME_RULES["soil_quality"]["depletion_rate"])

    # Apply energy saving
    if energy_saving > 0:
        state.energy = min(state.energy * (1 + energy_saving), GAME_RULES["max_energy"])

def process_action(state: GameState, shared_market: SharedMarket, action: dict) -> str:
    action_type = action['name']
    parameters = action['parameters']

    if action_type == "Plant":
        return plant_crop(state, Action(type="plant", details={"crop_type": parameters[0], "plot_index": int(parameters[1])}))
    elif action_type == "Harvest":
        return harvest_crop(state, Action(type="harvest", details={"plot_index": int(parameters[0])}))
    elif action_type == "Buy":
        if parameters[0] in GAME_RULES["cooperative_upgrades"]:
            return "Cooperative upgrades can only be purchased through a separate action"
        return buy_item(state, Action(type="buy", details={"item_type": parameters[0]}))
    elif action_type == "Sell":
        return sell_crops(state, shared_market, Action(type="sell", details={"crop_type": parameters[0], "amount": int(parameters[1]), "market_type": "local"}))
    elif action_type == "Rest":
        state.energy = min(state.energy + GAME_RULES["energy_regen_per_day"], GAME_RULES["max_energy"])
        return "Rested and regained some energy"
    elif action_type == "Maintenance":
        return perform_maintenance(state, Action(type="maintenance", details={"maintenance_type": parameters[0], "plot_index": int(parameters[1])}))
    else:
        return f"Unknown action type: {action_type}"
    
def process_cooperative_upgrade(player1_state: GameState, player2_state: GameState, shared_market: SharedMarket, action: dict) -> str:
    upgrade_type = action['parameters'][0]
    if upgrade_type not in GAME_RULES["cooperative_upgrades"]:
        return "Invalid cooperative upgrade"
    
    upgrade_cost = GAME_RULES["cooperative_upgrades"][upgrade_type]["cost"]
    if player1_state.money < upgrade_cost / 2 or player2_state.money < upgrade_cost / 2:
        return "Insufficient funds for cooperative upgrade"
    
    player1_state.money -= upgrade_cost / 2
    player2_state.money -= upgrade_cost / 2
    player1_state.upgrades.append(upgrade_type)
    player2_state.upgrades.append(upgrade_type)
    
    return f"Purchased cooperative upgrade: {upgrade_type}"

def update_game_state(state: GameState):
    process_day(state)