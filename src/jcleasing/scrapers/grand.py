"""Scraper for 235 Grand building."""

from datetime import datetime
from typing import List, Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from jcleasing.models.units import UnitInfo, PriceInfo
from jcleasing.scrapers.base import BaseScraper
from jcleasing.utils.helpers import wait, shorten_floorplan_type, get_current_timestamp


class Grand235Scraper(BaseScraper):
    """Scraper for 235 Grand building."""

    def get_units(self) -> List[UnitInfo]:
        """Get all available units from 235 Grand."""
        units = []
        for floorplan_type in [
            "studio",
            "1-bedroom---1-bathroom",
            "2-bedroom---2-bathroom",
        ]:
            self.driver.get(f"https://www.235grand.com/floorplans/{floorplan_type}")
            wait()

            # Wait for the table to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "table-card"))
            )

            # Get all unit rows
            unit_rows = self.driver.find_elements(
                by=By.CSS_SELECTOR, value=".table-card .unit-container"
            )

            for row in unit_rows:
                try:
                    unit_info = self._parse_unit_row(row)
                    if unit_info:
                        units.append(unit_info)
                except Exception as e:
                    print(f"Error parsing unit row: {e}")

        return units

    def _get_units_in_floorplan(self) -> List[UnitInfo]:
        """Get all units from the currently open floorplan modal."""
        try:
            # Wait for the units to load in the modal
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "unit-list"))
            )

            unit_rows = self.driver.find_elements(by=By.CLASS_NAME, value="unit-row")

            return [self._parse_unit_row(row) for row in unit_rows]

        except Exception as e:
            print(f"Error getting units in floorplan: {e}")
            return []

    def _parse_unit_row(self, row_element) -> Optional[UnitInfo]:
        """Parse unit information from a unit row."""
        try:
            # Extract unit number from the td-card-name element
            unit_cell = row_element.find_element(By.CLASS_NAME, "td-card-name")
            unit_number = unit_cell.text.strip().split("#")[-1].strip()

            # Extract price from the td-card-rent element
            price_cell = row_element.find_element(By.CLASS_NAME, "td-card-rent")
            price_text = price_cell.text.strip()

            # Extract both prices from the range
            prices = [
                p.strip().replace("$", "").replace(",", "")
                for p in price_text.split("to")
            ]
            price = prices[0]  # Lower price
            price_range = (
                f"{prices[0]} - {prices[1]}" if len(prices) > 1 else ""
            )  # Format with dash

            # Extract available date from the td-card-available element
            available_cell = row_element.find_element(
                By.CLASS_NAME, "td-card-available"
            )
            available_date = available_cell.text.strip()

            # Get floorplan type from parent element
            floorplan_type = self._get_element_text(
                row_element.find_element(By.XPATH, ".."),  # Get from parent element
                ".floorplan-section h2",
            )

            # Clean and format the data
            # price is already cleaned above

            # Parse the available date
            available_date = self._parse_available_date(available_date)

            # Create price info
            price_info = PriceInfo(
                price=price,
                price_range=price_range,
                date_fetched=get_current_timestamp(),
            )

            return UnitInfo(
                unit=unit_number,
                building="235Grand",
                available_date=available_date,
                floorplan_type=shorten_floorplan_type(floorplan_type),
                prices=[price_info],
            )

        except Exception as e:
            print(f"Error parsing unit row: {e}")
            return None

    @staticmethod
    def _parse_available_date(date_str: str) -> str:
        """Parse the available date string."""
        if not date_str or "now" in date_str.lower():
            return "1900-01-01"

        try:
            # Try to parse the date (format: "Available MM/DD/YYYY")
            date_part = date_str.lower().replace("available", "").strip()
            date_obj = datetime.strptime(date_part, "%m/%d/%Y")
            return date_obj.strftime("%Y-%m-%d")
        except ValueError:
            return "1900-01-01"
