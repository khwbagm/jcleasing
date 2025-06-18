#!/usr/bin/env python3
"""Main entry point for the jcleasing package."""

import json
import os
from datetime import datetime
from typing import Dict, List, Type, Optional

from logzero import logger

from jcleasing.browser.context import WebDriverContext
from jcleasing.models.units import UnitInfo
from jcleasing.scrapers.base import BaseScraper
from jcleasing.scrapers.columbus import ColumbusScraper
from jcleasing.scrapers.grand import Grand235Scraper
from jcleasing.scrapers.grove import GroveScraper
from jcleasing.scrapers.haus25 import Haus25Scraper
from jcleasing.scrapers.park import Park18Scraper
from jcleasing.scrapers.warren import WarrenAtYorkScraper


def save_results(results: Dict[str, List[UnitInfo]], output_dir: str = "data") -> str:
    """Save scraping results to a JSON file.

    Args:
        results: Dictionary mapping building names to lists of UnitInfo objects.
        output_dir: Directory to save the results in.

    Returns:
        Path to the saved file.
    """
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"results_{timestamp}.json")

    # Convert UnitInfo objects to dictionaries
    serializable_results = {}
    for building, units in results.items():
        serializable_results[building] = [
            {k: v for k, v in unit.__dict__.items() if not k.startswith("_")}
            for unit in units
            if unit is not None
        ]
        # Convert PriceInfo objects to dictionaries
        for unit_data in serializable_results[building]:
            if "prices" in unit_data and unit_data["prices"]:
                unit_data["prices"] = [
                    {k: v for k, v in price.__dict__.items() if not k.startswith("_")}
                    for price in unit_data["prices"]
                ]

    with open(output_path, "w") as f:
        json.dump(serializable_results, f, indent=2)

    return output_path


def get_available_scrapers() -> Dict[str, Type[BaseScraper]]:
    """Get a mapping of scraper names to their classes.

    Returns:
        Dictionary mapping scraper names to scraper classes.
    """
    return {
        "columbus579": ColumbusScraper,
        "haus25": Haus25Scraper,
        "1grove": GroveScraper,
        "warrenatyork": WarrenAtYorkScraper,
        "18park": Park18Scraper,
        "235grand": Grand235Scraper,
    }


def main(debug: bool = False):
    """Run all scrapers and save the results.

    Args:
        debug: Whether to run in debug mode (shows browser).
    """
    scrapers = get_available_scrapers()
    results = {}

    with WebDriverContext(debug=debug) as driver:
        for name, scraper_class in scrapers.items():
            try:
                logger.info(f"Scraping {name}...")
                scraper = scraper_class(driver)
                units = scraper.get_units()
                results[name] = units
                logger.info(f"Found {len(units)} units in {name}")
            except Exception as e:
                logger.error(f"Error scraping {name}: {e}")
                results[name] = []

    # Save results
    output_file = save_results(results)
    logger.info(f"Results saved to {output_file}")

    return results


if __name__ == "__main__":
    main(debug=False)
