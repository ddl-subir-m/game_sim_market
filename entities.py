from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict

class Crop(BaseModel):
    type: str
    planted_at: int
    growth_progress: float = 0
    quality: float = 1.0

    def is_mature(self, current_day: int, base_growth_time: int) -> bool:
        return (current_day - self.planted_at) >= base_growth_time

class Plot(BaseModel):
    soil_quality: float = 1.0
    crop: Optional[Crop] = None

    def is_vacant(self) -> bool:
        return self.crop is None

class SharedMarket(BaseModel):
    supply: Dict[str, int] = {}
    demand: Dict[str, int] = {}

class GameState(BaseModel):
    day: int = 1
    season: str = "Spring"
    weather: str = "Sunny"
    money: int = 0  # Will be set from GAME_RULES
    energy: int = 0  # Will be set from GAME_RULES
    plots: List[Plot] = [Plot()]
    harvested_crops: Dict[str, int] = {}
    upgrades: List[str] = []
    market_trends: Dict[str, float] = {}
    invalid_action_count: int = 0
    action_log: List[str] = []  # Add this line to store the player's action log

    def get_plot_status(self, game_rules: dict) -> List[str]:
        status = []
        for i, plot in enumerate(self.plots, start=1):
            if plot.crop is None:
                status.append(f"Plot {i}: Vacant")
            else:
                crop = plot.crop
                growth_percentage = min(100, crop.growth_progress * 100)
                maturity = "Mature" if crop.growth_progress >= 1.0 else "Growing"
                status.append(f"Plot {i}: {crop.type} ({maturity}, {growth_percentage:.1f}% grown)")
        return status

class Action(BaseModel):
    type: str
    details: Dict[str, Any] = {}