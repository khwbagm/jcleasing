"""Scraper for Columbus 579 building."""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from jcleasing.models.units import UnitInfo, PriceInfo
from jcleasing.scrapers.base import BaseScraper
from jcleasing.utils.helpers import (
    wait,
    shorten_floorplan_type,
    shorten_price,
    get_current_timestamp,
)


class ColumbusScraper(BaseScraper):
    """Scraper for Columbus 579 building."""

    BUILDING_URLS = [
        "https://ironstate.com/property/50-columbus",
        "https://ironstate.com/property/70-columbus",
        "https://ironstate.com/property/90-columbus",
    ]

    def get_units(self) -> List[UnitInfo]:
        """Get all available units from Columbus 579."""
        units = []
        for url_building in self.BUILDING_URLS:
            building_name = url_building.split("/")[-1]
            floorplan_urls = self._get_available_floorplans(url_building)
            for floorplan_url in floorplan_urls:
                units.extend(self._get_units_in_floorplan(floorplan_url, building_name))
        return units

    def _get_available_floorplans(self, building_url: str) -> List[str]:
        """Get all available floorplan URLs for a building."""
        url = f"{building_url}#floor-plans-property"
        self.driver.get(url)
        wait()

        floorplan_boxes = self.driver.find_elements(
            by=By.CSS_SELECTOR, value="div.floorplans-widget__box"
        )

        results = []
        for box in floorplan_boxes:
            links = box.find_elements(by=By.CSS_SELECTOR, value="a")
            for link in links:
                href = link.get_attribute("href")
                if href and "/floorplan/" in href:
                    results.append(href)
        return results

    def _get_units_in_floorplan(
        self, floorplan_url: str, building_name: str
    ) -> List[UnitInfo]:
        """Get all units from a specific floorplan."""
        self.driver.get(f"{floorplan_url}#units")
        wait()

        units = self.driver.find_elements(
            by=By.CSS_SELECTOR, value="article.splide__slide"
        )

        results = {}
        for unit in units:
            unit_info = self._parse_unit_html(unit)
            if unit_info:
                unit_info.building = building_name
                results[unit_info.unit] = unit_info
        return list(results.values())

    def _parse_unit_html(self, unit_element: Any) -> Optional[UnitInfo]:
        """Parse unit information from HTML element."""
        try:
            # Try to parse using the first format
            try:
                aval, unit, price_n_size_type, _ = unit_element.text.split("\n")
                price, size_type = price_n_size_type.split(" ", 1)
                size, floorplan_type = size_type.split(" sq. ft. ")
                unit = unit.split(" ")[1]
            except ValueError:
                # Fall back to second format
                text = unit_element.get_attribute("innerHTML").strip()
                lines = self._remove_html_tags(text).split("\n")
                vals = [x.strip() for x in lines if x.strip() != ""]

                if len(vals) == 5:
                    aval_unit, price, size, floorplan_type, _ = vals
                    aval, unit = aval_unit.lower().split("unit")
                    aval = aval.strip()
                    unit = unit.strip()
                elif len(vals) == 6:
                    aval, unit, price, size, floorplan_type, _ = vals
                else:
                    return None

            # Parse availability date
            if "now" in aval.lower():
                available_date = "1900-01-01"
            else:
                aval_date = aval.split(" ")[1]
                aval_m, aval_d, aval_y = aval_date.split("/")
                available_date = f"{int(aval_y)}-{int(aval_m):02d}-{int(aval_d):02d}"

            # Clean up values
            unit = unit.lower().replace("unit", "").strip()
            size = size.lower().replace("sq. ft.", "").replace(",", "").strip()

            # Create price info
            price_info = PriceInfo(
                price=int(shorten_price(price)),
                price_range="",
                date_fetched=get_current_timestamp(),
            )

            return UnitInfo(
                unit=unit,
                size=size,
                floorplan_type=shorten_floorplan_type(floorplan_type),
                available_date=available_date,
                prices=[price_info],
            )

        except Exception as e:
            print(f"Error parsing unit: {e}")
            return None

    @staticmethod
    def _remove_html_tags(text: str) -> str:
        """Remove HTML tags from a string."""
        return re.sub(r"<[^>]+>", "", text)
