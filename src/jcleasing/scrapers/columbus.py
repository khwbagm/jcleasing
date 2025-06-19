"""Scraper for Columbus 579 building."""

import re
from typing import List, Any, Optional

from loguru import logger
from selenium.webdriver.common.by import By

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
        logger.info("Starting Columbus units scraping")
        units = []
        for url_building in self.BUILDING_URLS:
            building_name = url_building.split("/")[-1]
            logger.info(f"Processing building: {building_name}")
            try:
                floorplan_urls = self._get_available_floorplans(url_building)
                logger.debug(
                    f"Found {len(floorplan_urls)} floorplans for {building_name}"
                )
                for floorplan_url in floorplan_urls:
                    try:
                        building_units = self._get_units_in_floorplan(
                            floorplan_url, building_name
                        )
                        units.extend(building_units)
                        logger.debug(
                            f"Found {len(building_units)} units in floorplan {floorplan_url}"
                        )
                    except Exception as e:
                        logger.error(
                            f"Error processing floorplan {floorplan_url}: {str(e)}",
                            exc_info=True,
                        )
            except Exception as e:
                logger.error(
                    f"Error processing building {building_name}: {str(e)}",
                    exc_info=True,
                )

        logger.info(f"Found {len(units)} units in total")
        return units

    def _get_available_floorplans(self, building_url: str) -> List[str]:
        """Get all available floorplan URLs for a building."""
        url = f"{building_url}#floor-plans-property"
        logger.debug(f"Fetching floorplans from {url}")

        try:
            self.driver.get(url)
            wait()

            floorplan_boxes = self.driver.find_elements(
                by=By.CSS_SELECTOR, value="div.floorplans-widget__box"
            )
            logger.debug(f"Found {len(floorplan_boxes)} floorplan boxes")

            results = []
            for box in floorplan_boxes:
                links = box.find_elements(by=By.CSS_SELECTOR, value="a")
                for link in links:
                    href = link.get_attribute("href")
                    if href and "/floorplan/" in href:
                        results.append(href)

            logger.debug(f"Found {len(results)} floorplan URLs")
            return results

        except Exception as e:
            logger.error(
                f"Error fetching floorplans from {url}: {str(e)}", exc_info=True
            )
            return []

    def _get_units_in_floorplan(
        self, floorplan_url: str, building_name: str
    ) -> List[UnitInfo]:
        """Get all units from a specific floorplan."""
        logger.debug(f"Fetching units from floorplan: {floorplan_url}")

        try:
            self.driver.get(f"{floorplan_url}#units")
            wait()

            units = self.driver.find_elements(
                by=By.CSS_SELECTOR, value="article.splide__slide"
            )
            logger.debug(f"Found {len(units)} unit elements")

            results = {}
            for unit in units:
                try:
                    unit_info = self._parse_unit_html(unit)
                    if unit_info:
                        unit_info.building = building_name
                        results[unit_info.unit] = unit_info
                        logger.debug(f"Successfully parsed unit: {unit_info.unit}")
                except Exception as e:
                    logger.error(f"Error parsing unit element: {str(e)}", exc_info=True)

            logger.info(f"Parsed {len(results)} unique units from floorplan")
            return list(results.values())

        except Exception as e:
            logger.error(
                f"Error fetching units from floorplan {floorplan_url}: {str(e)}",
                exc_info=True,
            )
            return []

    def _parse_unit_html(self, unit_element: Any) -> Optional[UnitInfo]:
        """Parse unit information from HTML element."""
        logger.debug("Parsing unit HTML element")

        try:
            # Try to parse using the first format
            try:
                aval, unit, price_n_size_type, _ = unit_element.text.split("\n")
                price, size_type = price_n_size_type.split(" ", 1)
                size, floorplan_type = size_type.split(" sq. ft. ")
                unit = unit.split(" ")[1]
                logger.debug(f"Parsed unit {unit} using first format")
            except ValueError:
                logger.debug("First format parsing failed, trying alternative format")
                # Fall back to second format
                text = unit_element.get_attribute("innerHTML").strip()
                lines = self._remove_html_tags(text).split("\n")
                vals = [x.strip() for x in lines if x.strip() != ""]

                if len(vals) == 5:
                    aval_unit, price, size, floorplan_type, _ = vals
                    aval, unit = aval_unit.lower().split("unit")
                    aval = aval.strip()
                    unit = unit.strip()
                    logger.debug(f"Parsed unit {unit} using 5-value format")
                elif len(vals) == 6:
                    aval, unit, price, size, floorplan_type, _ = vals
                    logger.debug(f"Parsed unit {unit} using 6-value format")
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
