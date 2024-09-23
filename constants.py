GAME_RULES = {
    # "total_days": 120,  # 4 seasons of 30 days each
    "total_days": 7,  
    "starting_money": 1000,
    "max_energy": 100,
    "energy_regen_per_day": 20,
    "seasons": ["Spring", "Summer", "Fall", "Winter"],
    "weather_types": ["Sunny", "Rainy", "Drought", "Storm"],
    "weather_probabilities": {
        "Spring": [0.5, 0.3, 0.1, 0.1],
        "Summer": [0.6, 0.1, 0.2, 0.1],
        "Fall": [0.4, 0.4, 0.1, 0.1],
        "Winter": [0.3, 0.3, 0.1, 0.3]
    },
    "crops": {
        "Wheat": {"cost": 10, "base_growth_time": 7, "base_yield": 5, "base_price": 30, "hardiness": 0.8},
        "Corn": {"cost": 15, "base_growth_time": 10, "base_yield": 8, "base_price": 25, "hardiness": 0.6},
        "Tomato": {"cost": 20, "base_growth_time": 6, "base_yield": 6, "base_price": 45, "hardiness": 0.5},
        "Potato": {"cost": 12, "base_growth_time": 8, "base_yield": 7, "base_price": 35, "hardiness": 0.9},
        "Strawberry": {"cost": 30, "base_growth_time": 5, "base_yield": 4, "base_price": 75, "hardiness": 0.4}
    },
    "energy_cost": {
        "plant": {"Wheat": 10, "Corn": 15, "Tomato": 12, "Potato": 8, "Strawberry": 20},
        "harvest": {"Wheat": 15, "Corn": 20, "Tomato": 18, "Potato": 12, "Strawberry": 25},
        "maintenance": {"water": 5, "weed": 10, "fertilize": 15},
        "trade": {"local": 5, "global": 10}
    },
    "weather_effects": {
        "Sunny": {"growth": 1.0, "yield": 1.1, "energy": 1.0},
        "Rainy": {"growth": 1.2, "yield": 1.0, "energy": 1.2},
        "Drought": {"growth": 0.8, "yield": 0.7, "energy": 1.5},
        "Storm": {"growth": 0.5, "yield": 0.8, "energy": 1.3}
    },
    "soil_quality": {
        "depletion_rate": 0.1,
        "maintenance_improvement": 0.2,
        "yield_factor": 0.5  # How much soil quality affects yield (0.5 means 50% impact)
    },
    "market": {
        "local_price_factor": 1.1,
        "global_price_factor": 1.3,
        "max_price_fluctuation": 0.2,
        "trend_duration": 7  # days
    },
    "upgrades": {
        "Irrigation": {"cost": 500, "water_saving": 0.2},
        "Greenhouse": {"cost": 1000, "weather_protection": 0.5},
        "Fertilizer": {"cost": 300, "yield_boost": 0.2},
        "Automation": {"cost": 800, "energy_saving": 0.15}
    },
    "cooperative_upgrades": {
        "Irrigation Network": {"cost": 2000, "water_saving": 0.3},
        "Shared Greenhouse": {"cost": 3000, "weather_protection": 0.7},
    },
    
    # New entry for plot purchase
    "plot_purchase": {
        "base_cost": 500,  # Base cost to buy a new plot
        "cost_increase_factor": 1.5  # Each subsequent plot costs 1.5 times more
    }
}