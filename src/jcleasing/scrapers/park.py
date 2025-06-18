"""Scraper for 18 Park building."""
import re
from datetime import datetime
from typing import List, Optional, Dict, Any

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from jcleasing.models.units import UnitInfo, PriceInfo
from jcleasing.scrapers.base import BaseScraper
from jcleasing.utils.helpers import wait, shorten_floorplan_type, get_current_timestamp


class Park18Scraper(BaseScraper):
    """Scraper for 18 Park building."""
    
    def get_units(self) -> List[UnitInfo]:
        """Get all available units from 18 Park."""
        self.driver.get("https://www.18parkave.com/floorplans")
        wait()
        
        # Wait for the floorplans to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "floorplan-container"))
        )
        
        # Get all floorplan sections
        floorplan_sections = self.driver.find_elements(
            by=By.CLASS_NAME,
            value="floorplan-section"
        )
        
        units = []
        for section in floorplan_sections:
            try:
                # Extract floorplan type
                floorplan_type = self._get_element_text(section, ".floorplan-type")
                
                # Get all units in this section
                unit_cards = section.find_elements(
                    by=By.CLASS_NAME,
                    value="unit-card"
                )
                
                for card in unit_cards:
                    unit = self._parse_unit_card(card, floorplan_type)
                    if unit:
                        units.append(unit)
                        
            except Exception as e:
                print(f"Error processing floorplan section: {e}")
                continue
                
        return units
    
    def _parse_unit_card(self, card_element, floorplan_type: str) -> Optional[UnitInfo]:
        """Parse unit information from a unit card."""
        try:
            # Extract unit information
            unit_number = self._get_element_text(card_element, ".unit-number")
            price = self._get_element_text(card_element, ".price")
            size = self._get_element_text(card_element, ".sqft")
            available_date = self._get_element_text(card_element, ".available-date")
            
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
                building="18Park",
                size=size,
                available_date=available_date,
                floorplan_type=shorten_floorplan_type(floorplan_type),
                prices=[price_info]
            )
            
        except Exception as e:
            print(f"Error parsing unit card: {e}")
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
