"""Scraper for KRE building."""

from typing import List, Optional

from loguru import logger
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from jcleasing.models.units import PriceInfo, UnitInfo
from jcleasing.scrapers.base import BaseScraper
from jcleasing.utils.basics import parse_availability_date
from jcleasing.utils.helpers import get_current_timestamp, shorten_floorplan_type, wait


class KREScraper(BaseScraper):
    """Scraper for KRE building."""

    def get_units(self) -> List[UnitInfo]:
        """Retrieve all available units from KRE building."""
        units = []

        for floorplan_type in self.floorplan_types:
            url = f"{self.base}/floorplans/{floorplan_type}"
            logger.info(f"Fetching units for floorplan type: {floorplan_type}")

            try:
                self.driver.get(url)
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
                        units.append(unit_info)
                        logger.debug(f"Successfully parsed unit: {unit_info.unit}")
                    except Exception as e:
                        logger.error(f"Error parsing unit row: {str(e)}", exc_info=True)

            except Exception as e:
                logger.error(
                    f"Error fetching units for floorplan {floorplan_type}: {str(e)}",
                    exc_info=True,
                )

        logger.info(f"Found {len(units)} units in total")
        return units

    def _parse_unit_row(self, row_element) -> Optional[UnitInfo]:
        """Parse unit information from a unit row element."""
        logger.debug("Parsing unit row")

        unit_cell = row_element.find_element(By.CLASS_NAME, "td-card-name")
        unit_number = unit_cell.text.strip().split("#")[-1].strip()

        price_cell = row_element.find_element(By.CLASS_NAME, "td-card-rent")
        price_text = price_cell.text.strip()
        prices = [
            p.strip().replace("$", "").replace(",", "") for p in price_text.split("to")
        ]
        price = prices[0]  # Lower price
        price_range = f"{prices[0]} - {prices[1]}" if len(prices) > 1 else ""

        available_cell = row_element.find_element(By.CLASS_NAME, "td-card-available")
        available_date = available_cell.text.strip()

        floorplan_type = self._get_element_text(
            row_element.find_element(By.XPATH, ".."),
            ".floorplan-section h2",
        )
        floorplan_type = shorten_floorplan_type(floorplan_type)

        return UnitInfo(
            unit=unit_number,
            building="235Grand",
            available_date=parse_availability_date(available_date),
            floorplan_type=floorplan_type,
            prices=[
                PriceInfo(
                    price=price,
                    price_range=price_range,
                    date_fetched=get_current_timestamp(),
                )
            ],
        )


class Grand235Scraper(KREScraper):
    base = "https://www.235grand.com"
    floorplan_types = [
        "studio",
        "1-bedroom---1-bathroom",
        "2-bedroom---2-bathroom",
    ]


class Park18Scraper(KREScraper):
    base = "https://www.18park.com"
    floorplan_types = [
        "studio",
        "1-bed-1-bath",
        "2-bed-2-bath",
    ]
