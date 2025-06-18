"""Scraper for Warren at York building."""

from datetime import datetime
from typing import List

from loguru import logger
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from jcleasing.models.units import PriceInfo, UnitInfo
from jcleasing.scrapers.base import BaseScraper
from jcleasing.utils.helpers import get_current_timestamp, shorten_floorplan_type, wait


class WarrenAtYorkScraper(BaseScraper):
    def get_units(self) -> List[UnitInfo]:
        self.driver.get(
            "https://www.windsorcommunities.com/properties/warren-at-york-by-windsor/floorplans/"
        )
        wait()

        # Click cookie acceptance button if present
        try:
            cookie_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            )
            cookie_button.click()
            wait()
        except (NoSuchElementException, TimeoutException):
            logger.warning("Cookie button not found or timed out")
            pass

        # Wait for units to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".spaces__unit"))
        )

        units = []
        unit_elements = self.driver.find_elements(By.CSS_SELECTOR, ".spaces__unit")

        for unit in unit_elements:
            try:
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

                try:
                    monthly_rent = float(raw_monthly_rent)
                except (ValueError, TypeError):
                    monthly_rent = None

                try:
                    square_feet = int(raw_square_feet)
                except (ValueError, TypeError):
                    square_feet = 0

                try:
                    available_date = datetime.strptime(
                        raw_available_date, "%B %d, %Y"
                    ).date()
                except (ValueError, TypeError):
                    available_date = "1900-01-01"

                units.append(
                    UnitInfo(
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
                )
            except Exception as e:
                print(f"Error parsing unit: {e}")
                continue

        return units
