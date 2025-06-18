"""Result handling and serialization for scraping data."""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional

from logzero import logger

from jcleasing.models.units import UnitInfo


def save_results(results: Dict[str, List[UnitInfo]], output_dir: str = "data") -> str:
    """Save scraping results to a JSON file.

    Args:
        results: Dictionary mapping building names to lists of UnitInfo objects.
        output_dir: Directory to save the results in.

    Returns:
        Path to the saved file.
    """
    manager = ResultsManager(output_dir)
    return manager.save(results)


class ResultsManager:
    """Manages saving and loading of scraping results."""

    def __init__(self, output_dir: str = "data"):
        """Initialize the results manager.

        Args:
            output_dir: Directory to save results in.
        """
        self.output_dir = output_dir

    def save(
        self, results: Dict[str, List[UnitInfo]], filename: Optional[str] = None
    ) -> str:
        """Save scraping results to a JSON file.

        Args:
            results: Dictionary mapping building names to lists of UnitInfo objects.
            filename: Optional filename. If not provided, uses timestamp.

        Returns:
            Path to the saved file.
        """
        os.makedirs(self.output_dir, exist_ok=True)

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"results_{timestamp}.json"

        output_path = os.path.join(self.output_dir, filename)

        # Convert UnitInfo objects to dictionaries
        serializable_results = self._serialize_results(results)

        with open(output_path, "w") as f:
            json.dump(serializable_results, f, indent=2)

        logger.info(f"Results saved to {output_path}")
        return output_path

    def _serialize_results(self, results: Dict[str, List[UnitInfo]]) -> Dict:
        """Convert UnitInfo objects to serializable dictionaries.

        Args:
            results: Raw results with UnitInfo objects.

        Returns:
            Serializable dictionary representation.
        """
        serializable_results = {}
        for building, units in results.items():
            serializable_results[building] = [
                {k: v for k, v in unit.__dict__.items() if not k.startswith("_")}
                for unit in units
                if unit is not None
            ]
            # Convert PriceInfo objects to dictionaries
            for unit_data in serializable_results[building]:
                if "prices" in unit_data and unit_data["prices"]:
                    unit_data["prices"] = [
                        {
                            k: v
                            for k, v in price.__dict__.items()
                            if not k.startswith("_")
                        }
                        for price in unit_data["prices"]
                    ]

        return serializable_results

    def load(self, filename: str) -> Dict:
        """Load results from a JSON file.

        Args:
            filename: Name of the file to load.

        Returns:
            Loaded results dictionary.
        """
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "r") as f:
            return json.load(f)

    def list_results(self) -> List[str]:
        """List all result files in the output directory.

        Returns:
            List of result filenames.
        """
        if not os.path.exists(self.output_dir):
            return []

        return [
            f
            for f in os.listdir(self.output_dir)
            if f.startswith("results_") and f.endswith(".json")
        ]
