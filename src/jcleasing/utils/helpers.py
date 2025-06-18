"""Helper functions for the jcleasing package."""
import time
import random
import re
from typing import Optional


def wait(b: float = 0.2, a: float = 1.0) -> None:
    """Wait for a random amount of time.
    
    Args:
        b: Base wait time in seconds.
        a: Additional random time range in seconds.
    """
    time.sleep(b + random.random() * a)


def shorten_floorplan_type(fpt: str) -> str:
    """Shorten floorplan type string to a standardized format.
    
    Args:
        fpt: Floorplan type string.
        
    Returns:
        str: Shortened floorplan type.
    """
    fpt = fpt.lower()
    if "studio" in fpt:
        return "studio"
    return (
        fpt.replace("s", "")
        .replace("bath", "b")
        .replace("bedroom", "b")
        .replace("bed", "b")
        .replace(" ", "")
        .replace(",", "")
        .replace("/", "")
    )


def shorten_price(price_str: str) -> str:
    """Remove currency symbols and formatting from price string.
    
    Args:
        price_str: Price string with formatting.
        
    Returns:
        str: Cleaned price string.
    """
    return price_str.replace(",", "").replace("$", "")


def get_current_timestamp() -> str:
    """Get current timestamp in YYYY-MM-DD HH:MM:SS format.
    
    Returns:
        str: Formatted timestamp string.
    """
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
