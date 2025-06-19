"""Base scraper class for all building scrapers."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By

from jcleasing.models.units import UnitInfo, PriceInfo
from jcleasing.utils.decorators import exception_helper


class BaseScraper(ABC):
    """Abstract base class for all building scrapers."""
    
    def __init__(self, driver: WebDriver):
        """Initialize the scraper with a WebDriver instance.
        
        Args:
            driver: Selenium WebDriver instance.
        """
        self.driver = driver
    
    @abstractmethod
    def get_units(self) -> List[UnitInfo]:
        """Get all available units from the building.
        
        Returns:
            List of UnitInfo objects representing available units.
        """
        pass
    
    @exception_helper
    def _get_element_text(self, element: Any, selector: str, default: str = "") -> str:
        """Safely get text from an element using a CSS selector.
        
        Args:
            element: Parent element or WebDriver.
            selector: CSS selector to find the element.
            default: Default value if element is not found.
            
        Returns:
            Text content of the element or default value.
        """
        try:
            elem = element.find_element(By.CSS_SELECTOR, selector)
            return elem.text.strip() if elem else default
        except Exception:
            return default
    
    @exception_helper
    def _get_element_attribute(self, element: Any, selector: str, attribute: str, default: str = "") -> str:
        """Safely get an attribute from an element using a CSS selector.
        
        Args:
            element: Parent element or WebDriver.
            selector: CSS selector to find the element.
            attribute: Name of the attribute to get.
            default: Default value if element or attribute is not found.
            
        Returns:
            Attribute value or default.
        """
        try:
            elem = element.find_element(By.CSS_SELECTOR, selector)
            return elem.get_attribute(attribute) or default
        except Exception:
            return default
