"""Scraper for Warren at York building."""
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


class WarrenAtYorkScraper(BaseScraper):
    """Scraper for Warren at York building."""
    
    def get_units(self) -> List[UnitInfo]:
        """Get all available units from Warren at York."""
        self.driver.get("https://www.warrenatyork.com/floorplans")
        wait()
        
        # Extract CSRF token for API requests
        csrf_token = self._get_csrf_token()
        if not csrf_token:
            print("Could not get CSRF token")
            return []
        
        # Make API request to get available units
        headers = {
            "X-CSRF-TOKEN": csrf_token,
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest"
        }
        
        # Get property ID from the page
        property_id = self._get_property_id()
        if not property_id:
            print("Could not get property ID")
            return []
        
        # Make API request to get available units
        api_url = f"https://www.warrenatyork.com/api/units/available?property_id={property_id}"
        self.driver.execute_script("""
            var callback = arguments[arguments.length - 1];
            fetch(arguments[0], {
                method: 'GET',
                headers: arguments[1],
                credentials: 'include'
            })
            .then(response => response.json())
            .then(data => callback({status: 'success', data: data}))
            .catch(error => callback({status: 'error', error: error.toString()}));
        """, api_url, headers)
        
        # Wait for the response
        response = self.driver.execute_async_script("""
            var callback = arguments[arguments.length - 1];
            window.unitsCallback = function(data) {
                callback({status: 'success', data: data});
            };
            window.unitsError = function(error) {
                callback({status: 'error', error: error});
            };
            
            // The actual API call will be made by the page's JavaScript
            // and will call our callback when done
            return true;
        """)
        
        if response.get('status') != 'success':
            print(f"API request failed: {response.get('error')}")
            return []
            
        units_data = response.get('data', {}).get('data', [])
        return [self._parse_unit_data(unit) for unit in units_data]
    
    def _get_csrf_token(self) -> Optional[str]:
        """Extract CSRF token from the page."""
        try:
            meta = self.driver.find_element(
                by=By.CSS_SELECTOR,
                value="meta[name='csrf-token']"
            )
            return meta.get_attribute("content")
        except Exception as e:
            print(f"Error getting CSRF token: {e}")
            return None
    
    def _get_property_id(self) -> Optional[str]:
        """Extract property ID from the page."""
        try:
            # Look for property ID in the page source
            page_source = self.driver.page_source
            match = re.search(r'property_id[\s=:"\']+(\d+)', page_source)
            if match:
                return match.group(1)
                
            # Alternative: Check for a data attribute on the body
            return self.driver.find_element(
                by=By.TAG_NAME,
                value="body"
            ).get_attribute("data-property-id")
            
        except Exception as e:
            print(f"Error getting property ID: {e}")
            return None
    
    def _parse_unit_data(self, unit_data: Dict[str, Any]) -> UnitInfo:
        """Parse unit information from API response."""
        try:
            # Extract basic information
            unit_number = unit_data.get('unit_number', '')
            price = str(unit_data.get('price', '0'))
            size = str(unit_data.get('square_feet', '0'))
            available_date = unit_data.get('available_date', '')
            floorplan_name = unit_data.get('floor_plan_name', '')
            
            # Clean and format the data
            price = price.replace("$", "").replace(",", "").strip()
            size = size.replace(",", "").strip()
            
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
                building="WarrenAtYork",
                size=size,
                available_date=available_date,
                floorplan_type=shorten_floorplan_type(floorplan_name),
                prices=[price_info]
            )
            
        except Exception as e:
            print(f"Error parsing unit data: {e}")
            return None
    
    @staticmethod
    def _parse_available_date(date_str: str) -> str:
        """Parse the available date string."""
        if not date_str or "now" in date_str.lower():
            return "1900-01-01"
        
        try:
            # Try to parse the date (format: "YYYY-MM-DD" or "MM/DD/YYYY")
            date_str = date_str.strip()
            if "-" in date_str:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            else:
                date_obj = datetime.strptime(date_str, "%m/%d/%Y")
                
            return date_obj.strftime("%Y-%m-%d")
        except ValueError:
            return "1900-01-01"
