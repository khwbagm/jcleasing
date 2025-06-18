"""Main orchestration logic for running scrapers."""

from typing import Dict, List, Optional, Set

from logzero import logger

from jcleasing.browser.context import WebDriverContext
from jcleasing.core.registry import ScraperRegistry
from jcleasing.core.results import ResultsManager
from jcleasing.models.units import UnitInfo


def run_scrapers(
    debug: bool = False, output_dir: str = "data", scrapers: Optional[List[str]] = None
) -> Dict[str, List[UnitInfo]]:
    """Run scrapers and return the results.

    Args:
        debug: Whether to run in debug mode (shows browser).
        output_dir: Directory to save results in.
        scrapers: List of specific scrapers to run. If None, runs all.

    Returns:
        Dictionary mapping scraper names to lists of UnitInfo objects.
    """
    runner = ScrapingRunner(debug=debug, output_dir=output_dir)
    return runner.run(scrapers)


class ScrapingRunner:
    """Handles the orchestration of scraping operations."""

    def __init__(self, debug: bool = False, output_dir: str = "data"):
        """Initialize the scraping runner.

        Args:
            debug: Whether to run in debug mode.
            output_dir: Directory to save results in.
        """
        self.debug = debug
        self.output_dir = output_dir
        self.registry = ScraperRegistry()
        self.results_manager = ResultsManager(output_dir)

    def run(
        self, scraper_names: Optional[List[str]] = None
    ) -> Dict[str, List[UnitInfo]]:
        """Run scrapers and collect results.

        Args:
            scraper_names: List of specific scrapers to run. If None, runs all.

        Returns:
            Dictionary mapping scraper names to lists of UnitInfo objects.
        """
        # Determine which scrapers to run
        available_scrapers = self.registry.get_all()

        if scraper_names is None:
            scrapers_to_run = available_scrapers
        else:
            scrapers_to_run = self._filter_scrapers(available_scrapers, scraper_names)

        if not scrapers_to_run:
            logger.warning("No scrapers to run")
            return {}

        logger.info(
            f"Running {len(scrapers_to_run)} scrapers: {list(scrapers_to_run.keys())}"
        )

        # Run scrapers
        results = {}
        with WebDriverContext(debug=self.debug) as driver:
            for name, scraper_class in scrapers_to_run.items():
                results[name] = self._run_single_scraper(name, scraper_class, driver)

        return results

    def run_and_save(self, scraper_names: Optional[List[str]] = None) -> str:
        """Run scrapers and save results to file.

        Args:
            scraper_names: List of specific scrapers to run. If None, runs all.

        Returns:
            Path to the saved results file.
        """
        results = self.run(scraper_names)
        return self.results_manager.save(results)

    def _filter_scrapers(
        self, available_scrapers: Dict, requested_names: List[str]
    ) -> Dict:
        """Filter scrapers based on requested names.

        Args:
            available_scrapers: All available scrapers.
            requested_names: Names of scrapers to include.

        Returns:
            Dictionary of filtered scrapers.
        """
        scrapers_to_run = {}
        available_names = set(available_scrapers.keys())
        requested_set = set(requested_names)

        # Check for invalid scraper names
        invalid_names = requested_set - available_names
        if invalid_names:
            logger.warning(f"Unknown scrapers: {invalid_names}")
            logger.info(f"Available scrapers: {available_names}")

        # Include only valid scrapers
        valid_names = requested_set & available_names
        for name in valid_names:
            scrapers_to_run[name] = available_scrapers[name]

        return scrapers_to_run

    def _run_single_scraper(self, name: str, scraper_class, driver) -> List[UnitInfo]:
        """Run a single scraper and handle errors.

        Args:
            name: Name of the scraper.
            scraper_class: Scraper class to instantiate.
            driver: WebDriver instance.

        Returns:
            List of UnitInfo objects or empty list on error.
        """
        try:
            logger.info(f"Scraping {name}...")
            scraper = scraper_class(driver)
            units = scraper.get_units()
            logger.info(f"Found {len(units)} units in {name}")
            return units
        except Exception as e:
            logger.error(f"Error scraping {name}: {e}")
            return []

    def list_available_scrapers(self) -> List[str]:
        """Get list of available scraper names.

        Returns:
            List of scraper names.
        """
        return self.registry.list_names()
