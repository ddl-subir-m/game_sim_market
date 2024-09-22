from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict

class Crop(BaseModel):
    type: str
    planted_at: int
    growth_progress: float = 0
    quality: float = 1.0

class Plot(BaseModel):
    soil_quality: float = 1.0
    crop: Optional[Crop] = None

class SharedMarket(BaseModel):
    supply: Dict[str, int] = {}
    demand: Dict[str, int] = {}

class GameState(BaseModel):
    day: int = 1
    season: str = "Spring"
    weather: str = "Sunny"
    money: int = 0  # Will be set from GAME_RULES
    energy: int = 0  # Will be set from GAME_RULES
    plots: List[Plot] = []
    harvested_crops: Dict[str, int] = {}
    upgrades: List[str] = []
    market_trends: Dict[str, float] = {}

class Action(BaseModel):
    type: str
    details: Dict[str, Any] = {}