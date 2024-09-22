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

    def get_plot_status(self, game_rules: dict) -> List[str]:
        status = []
        for i, plot in enumerate(self.plots, start=1):
            if plot.is_vacant():
                status.append(f"Plot {i}: Vacant")
            else:
                crop = plot.crop
                base_growth_time = game_rules["crops"][crop.type]["base_growth_time"]
                growth_percentage = min(100, ((self.day - crop.planted_at) / base_growth_time) * 100)
                maturity = "Mature" if crop.is_mature(self.day, base_growth_time) else "Growing"
                status.append(f"Plot {i}: {crop.type} ({maturity}, {growth_percentage:.1f}% grown)")
        return status

class Action(BaseModel):
    type: str
    details: Dict[str, Any] = {}