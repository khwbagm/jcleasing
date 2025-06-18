"""Scraper for Haus25 building."""
from datetime import datetime
from typing import List, Dict, Any, Optional

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from jcleasing.models.units import UnitInfo, PriceInfo
from jcleasing.scrapers.base import BaseScraper
from jcleasing.utils.helpers import wait, get_current_timestamp


class Haus25Scraper(BaseScraper):
    """Scraper for Haus25 building."""
    
    def get_units(self) -> List[UnitInfo]:
        """Get all available units from Haus25."""
        floorplan_urls = self._get_available_floorplans()
        units = []
        
        for url in floorplan_urls:
            units.extend(self._get_units_in_floorplan(url))
            
        return units
    
    def _get_available_floorplans(self) -> List[str]:
        """Get all available floorplan URLs."""
        self.driver.get("https://livehaus25.com/availability/")
        wait()
        
        # Wait for the page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "availability-grid"))
        )
        
        # Extract all floorplan URLs
        floorplan_links = self.driver.find_elements(
            by=By.CSS_SELECTOR,
            value="a[href*='availability-detail']"
        )
        
        return list({link.get_attribute("href") for link in floorplan_links})
    
    def _get_units_in_floorplan(self, floorplan_url: str) -> List[UnitInfo]:
        """Get all units from a specific floorplan."""
        self.driver.get(floorplan_url)
        wait()
        
        # Wait for the page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "unit-card"))
        )
        
        units = self.driver.find_elements(
            by=By.CLASS_NAME,
            value="unit-card"
        )
        
        return [self._parse_unit_card(card) for card in units if self._is_unit_available(card)]
    
    def _is_unit_available(self, unit_element: Any) -> bool:
        """Check if a unit is available."""
        try:
            status = unit_element.find_element(
                by=By.CLASS_NAME,
                value="unit-status"
            ).text.lower()
            return "available" in status
        except:
            return False
    
    def _parse_unit_card(self, unit_element: Any) -> UnitInfo:
        """Parse unit information from a unit card."""
        try:
            # Extract basic information
            unit_number = self._get_element_text(unit_element, ".unit-number")
            price = self._get_element_text(unit_element, ".price")
            size = self._get_element_text(unit_element, ".sqft")
            available_date = self._get_element_text(unit_element, ".available-date")
            floorplan_type = self._get_element_text(unit_element, ".floorplan-type")
            
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
                building="Haus25",
                size=size,
                available_date=available_date,
                floorplan_type=floorplan_type,
                prices=[price_info]
            )
            
        except Exception as e:
            print(f"Error parsing unit card: {e}")
            return None
    
    @staticmethod
    def _parse_available_date(date_str: str) -> str:
        """Parse the available date string."""
        if not date_str or "immediately" in date_str.lower():
            return "1900-01-01"
        
        try:
            # Try to parse the date (format: "Available MM/DD/YYYY")
            date_part = date_str.lower().replace("available", "").strip()
            date_obj = datetime.strptime(date_part, "%m/%d/%Y")
            return date_obj.strftime("%Y-%m-%d")
        except ValueError:
            return "1900-01-01"
