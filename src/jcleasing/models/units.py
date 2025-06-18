"""Data models for apartment units and pricing information."""
from dataclasses import dataclass
from typing import List


@dataclass
class PriceInfo:
    """Represents pricing information for a unit."""
    price: int = 0
    price_range: str = ""
    date_fetched: str = ""


@dataclass
class UnitInfo:
    """Represents information about an apartment unit."""
    unit: str = ""
    building: str = ""
    size: int = 0
    available_date: str = ""
    floorplan_type: str = ""
    floorplan_link: str = ""
    floorplan_note: str = ""
    prices: List[PriceInfo] = None
    
    def __post_init__(self):
        if self.prices is None:
            self.prices = []
