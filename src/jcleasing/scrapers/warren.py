"""Scraper for Warren at York building."""

from datetime import datetime
from typing import List, Optional

from loguru import logger
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from jcleasing.models.units import PriceInfo, UnitInfo
from jcleasing.scrapers.base import BaseScraper
from jcleasing.utils.helpers import get_current_timestamp, shorten_floorplan_type, wait


class WarrenAtYorkScraper(BaseScraper):
    """Scraper for Warren at York building."""

    def get_units(self) -> List[UnitInfo]:
        """Get all available units from Warren at York."""
        logger.info("Fetching units from Warren at York")

        self.driver.get(
            "https://www.windsorcommunities.com/properties/warren-at-york-by-windsor/floorplans/"
        )
        wait()

        self._handle_cookie_banner()

        # Wait for units to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".spaces__unit"))
        )

        units = []
        unit_elements = self.driver.find_elements(By.CSS_SELECTOR, ".spaces__unit")

        for unit in unit_elements:
            try:
                unit_info = self._parse_unit_element(unit)
                if unit_info:
                    units.append(unit_info)
                    logger.debug(f"Successfully parsed unit: {unit_info.unit}")
            except Exception as e:
                logger.error(f"Error parsing unit: {e}", exc_info=True)
                continue

        logger.info(f"Found {len(units)} units")
        return units

    def _handle_cookie_banner(self) -> None:
        """Handle cookie acceptance banner if present."""
        try:
            cookie_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            )
            cookie_button.click()
            wait()
        except (NoSuchElementException, TimeoutException):
            logger.warning("Cookie button not found or timed out")
            pass

    def _parse_unit_element(self, unit) -> Optional[UnitInfo]:
        """Parse unit information from a unit element using the original working logic."""
        raw_monthly_rent = unit.find_element(
            By.CSS_SELECTOR, ".spaces__label-price a[data-spaces-unit-price]"
        ).get_attribute("data-spaces-unit-price")

        raw_available_date = (
            unit.find_element(By.CSS_SELECTOR, ".spaces__label-available-on")
            .text.split(",")[-1]
            .strip()
        )

        raw_square_feet = unit.find_element(
            By.CSS_SELECTOR, ".spaces__plan__attributes-area"
        ).text.split(" ")[0]

        monthly_rent = self._parse_monthly_rent(raw_monthly_rent)
        square_feet = self._parse_square_feet(raw_square_feet)
        available_date = self._parse_available_date(raw_available_date)

        return UnitInfo(
            unit=unit.get_attribute("data-spaces-unit"),
            building="Warren at York",
            size=square_feet,
            available_date=available_date,
            floorplan_type=shorten_floorplan_type(
                unit.get_attribute("data-spaces-sort-plan-name")
            ),
            prices=[
                PriceInfo(
                    price=monthly_rent,
                    date_fetched=get_current_timestamp(),
                )
            ],
        )

    def _parse_monthly_rent(self, raw_monthly_rent: str) -> Optional[float]:
        """Parse monthly rent using original logic."""
        try:
            return float(raw_monthly_rent)
        except (ValueError, TypeError):
            return None

    def _parse_square_feet(self, raw_square_feet: str) -> int:
        """Parse square feet using original logic."""
        try:
            return int(raw_square_feet)
        except (ValueError, TypeError):
            return 0

    def _parse_available_date(self, raw_available_date: str) -> str:
        """Parse available date using original logic."""
        try:
            available_date = datetime.strptime(raw_available_date, "%B %d, %Y").date()
            return available_date.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            return "1900-01-01"
