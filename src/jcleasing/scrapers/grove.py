"""Scraper for 1 Grove building."""
from datetime import datetime
from typing import List, Optional

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from jcleasing.models.units import UnitInfo, PriceInfo
from jcleasing.scrapers.base import BaseScraper
from jcleasing.utils.helpers import wait, shorten_floorplan_type, get_current_timestamp


class GroveScraper(BaseScraper):
    """Scraper for 1 Grove building."""
    
    def get_units(self) -> List[UnitInfo]:
        """Get all available units from 1 Grove."""
        self.driver.get("https://www.1grove.com/floorplans")
        wait()
        
        # Wait for the floorplans to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "floorplan-card"))
        )
        
        # Get all floorplan cards
        floorplan_cards = self.driver.find_elements(
            by=By.CLASS_NAME,
            value="floorplan-card"
        )
        
        units = []
        for card in floorplan_cards:
            try:
                # Click on the floorplan to see available units
                card.click()
                wait(1, 0.5)  # Wait for the modal to open
                
                # Get units in this floorplan
                units.extend(self._get_units_in_floorplan())
                
                # Close the modal
                close_btn = self.driver.find_element(
                    by=By.CSS_SELECTOR,
                    value="button[aria-label='Close']"
                )
                close_btn.click()
                wait()
                
            except Exception as e:
                print(f"Error processing floorplan: {e}")
                continue
                
        return units
    
    def _get_units_in_floorplan(self) -> List[UnitInfo]:
        """Get all units from the currently open floorplan modal."""
        try:
            # Wait for the units to load in the modal
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "unit-row"))
            )
            
            unit_rows = self.driver.find_elements(
                by=By.CLASS_NAME,
                value="unit-row"
            )
            
            return [self._parse_unit_row(row) for row in unit_rows]
            
        except Exception as e:
            print(f"Error getting units in floorplan: {e}")
            return []
    
    def _parse_unit_row(self, row_element) -> Optional[UnitInfo]:
        """Parse unit information from a unit row."""
        try:
            # Extract unit information
            unit_number = self._get_element_text(row_element, ".unit-number")
            price = self._get_element_text(row_element, ".price")
            size = self._get_element_text(row_element, ".sqft")
            available_date = self._get_element_text(row_element, ".available-date")
            floorplan_type = self._get_element_text(row_element, ".floorplan-type")
            
            # Clean and format the data
            unit_number = unit_number.replace("Unit ", "").strip()
            price = price.replace("$", "").replace(",", "").strip()
            size = size.replace("sq ft", "").replace(",", "").strip()
            
            # Parse the available date
            available_date = self._parse_available_date(available_date)
            
            # Create price info
            price_info = PriceInfo(
                price=price,
                price_range="",
                date_fetched=get_current_timestamp()
            )
            
            return UnitInfo(
                unit=unit_number,
                building="1Grove",
                size=size,
                available_date=available_date,
                floorplan_type=shorten_floorplan_type(floorplan_type),
                prices=[price_info]
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
