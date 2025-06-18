"""Scraper registry and management."""

from typing import Dict, List, Type, Optional

from jcleasing.scrapers.base import BaseScraper
from jcleasing.scrapers.columbus import ColumbusScraper
from jcleasing.scrapers.grand import Grand235Scraper
from jcleasing.scrapers.grove import GroveScraper
from jcleasing.scrapers.haus25 import Haus25Scraper
from jcleasing.scrapers.park import Park18Scraper
from jcleasing.scrapers.warren import WarrenAtYorkScraper


def get_available_scrapers() -> Dict[str, Type[BaseScraper]]:
    """Get a mapping of scraper names to their classes.

    Returns:
        Dictionary mapping scraper names to scraper classes.
    """
    registry = ScraperRegistry()
    return registry.get_all()


class ScraperRegistry:
    """Registry for managing available scrapers."""

    def __init__(self):
        """Initialize the scraper registry with default scrapers."""
        self._scrapers: Dict[str, Type[BaseScraper]] = {}
        self._register_default_scrapers()

    def _register_default_scrapers(self):
        """Register all default scrapers."""
        default_scrapers = {
            # "columbus579": ColumbusScraper,
            # "haus25": Haus25Scraper,
            # "1grove": GroveScraper,
            # "warrenatyork": WarrenAtYorkScraper,
            # "18park": Park18Scraper,
            "235grand": Grand235Scraper,
        }

        for name, scraper_class in default_scrapers.items():
            self.register(name, scraper_class)

    def register(self, name: str, scraper_class: Type[BaseScraper]):
        """Register a new scraper.

        Args:
            name: Name of the scraper.
            scraper_class: Scraper class that inherits from BaseScraper.

        Raises:
            ValueError: If scraper_class is not a subclass of BaseScraper.
        """
        if not issubclass(scraper_class, BaseScraper):
            raise ValueError(
                f"Scraper class {scraper_class} must inherit from BaseScraper"
            )

        self._scrapers[name] = scraper_class

    def unregister(self, name: str):
        """Unregister a scraper.

        Args:
            name: Name of the scraper to unregister.
        """
        if name in self._scrapers:
            del self._scrapers[name]

    def get(self, name: str) -> Optional[Type[BaseScraper]]:
        """Get a scraper class by name.

        Args:
            name: Name of the scraper.

        Returns:
            Scraper class if found, None otherwise.
        """
        return self._scrapers.get(name)

    def get_all(self) -> Dict[str, Type[BaseScraper]]:
        """Get all registered scrapers.

        Returns:
            Dictionary mapping scraper names to scraper classes.
        """
        return self._scrapers.copy()

    def list_names(self) -> List[str]:
        """Get a list of all registered scraper names.

        Returns:
            List of scraper names.
        """
        return list(self._scrapers.keys())

    def is_registered(self, name: str) -> bool:
        """Check if a scraper is registered.

        Args:
            name: Name of the scraper.

        Returns:
            True if registered, False otherwise.
        """
        return name in self._scrapers
