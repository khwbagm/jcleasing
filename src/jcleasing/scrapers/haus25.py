"""Scraper for Haus25 building."""

import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

from loguru import logger
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from jcleasing.models.units import UnitInfo, PriceInfo
from jcleasing.scrapers.base import BaseScraper
from jcleasing.utils.helpers import wait, get_current_timestamp


class Haus25Scraper(BaseScraper):
    """Scraper for Haus25 building."""

    def _get_all_floorplans(self):
        # Navigate to the site
        self.driver.get(
            "https://verisresidential.com/jersey-city-nj-apartments/haus25/"
        )
        wait()

        self.driver.execute_script("window.scrollBy(0, window.innerHeight);")
        wait()
        # Click the "View all" button to open the popup

        time.sleep(10)
        self.driver.find_element(
            by=By.CSS_SELECTOR, value="p.prop-details-search-view-all"
        ).click()

        # Identify the div with class "wp-block-group view-all-modal-content"
        try:
            modal_content_div = self.driver.find_element(
                By.CSS_SELECTOR, "div.wp-block-group.view-all-modal-content"
            )
            logger.debug("Found the view-all-modal-content div.")
        except Exception as e:
            logger.error(f"Could not find the view-all-modal-content div: {str(e)}")
            return []

        # Find all <div> elements with class containing "display-floorplan-details" inside modal_content_div
        floorplan_details_divs = modal_content_div.find_elements(
            By.XPATH, ".//div[contains(@class, 'display-floorplan-details')]"
        )
        return floorplan_details_divs

    def get_units(self) -> List[UnitInfo]:
        units: List[UnitInfo] = []

        # For each floorplan, click to trigger the ajax request, then capture the response
        for fp_div in self._get_all_floorplans():
            fp_json = get_ajax_response_json(self.driver, fp_div)
            parsed_units = parse_fp_json(fp_json)
            units.extend(parsed_units)

        return units


def parse_availability_date(date_str: str) -> str:
    """
    Parse availability date and format as YYYY-MM-DD.
    Returns '1970-01-01' if date is empty, invalid, or indicates immediate availability.

    Args:
        date_str: Date string in MM/DD/YYYY format or other formats

    Returns:
        Formatted date string as YYYY-MM-DD or '1970-01-01' for immediate availability
    """
    if not date_str or not date_str.strip():
        return "1970-01-01"

    date_str = date_str.strip()

    # Check for common indicators of immediate availability
    immediate_indicators = [
        "available now",
        "now",
        "immediate",
        "today",
        "asap",
        "available immediately",
        "move-in ready",
    ]

    if date_str.lower() in immediate_indicators:
        return "1970-01-01"

    # Try to parse MM/DD/YYYY format (most common)
    try:
        parsed_date = datetime.strptime(date_str, "%m/%d/%Y")
        return parsed_date.strftime("%Y-%m-%d")
    except ValueError:
        pass

    # Try to parse other common formats
    date_formats = [
        "%Y-%m-%d",  # Already in correct format
        "%m-%d-%Y",  # MM-DD-YYYY
        "%d/%m/%Y",  # DD/MM/YYYY
        "%Y/%m/%d",  # YYYY/MM/DD
        "%B %d, %Y",  # January 1, 2024
        "%b %d, %Y",  # Jan 1, 2024
        "%m/%d/%y",  # MM/DD/YY
        "%m-%d-%y",  # MM-DD-YY
    ]

    for date_format in date_formats:
        try:
            parsed_date = datetime.strptime(date_str, date_format)
            return parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            continue

    # If all parsing attempts fail, treat as immediate availability
    logger.warning(
        f"Could not parse date '{date_str}', treating as immediate availability"
    )
    return "1970-01-01"


def parse_fp_json(fp_json: Dict[str, Any]) -> List[UnitInfo]:
    """
    Parse floorplan JSON data and convert to UnitInfo objects.

    Args:
        fp_json: Dictionary containing floorplan data from AJAX response

    Returns:
        List of UnitInfo objects parsed from the JSON data
    """
    units = []

    try:
        # Extract basic property information
        building = fp_json.get("property_title", "")
        beds = fp_json.get("beds", "")
        baths = fp_json.get("baths", "")
        sqft = fp_json.get("sqft", "")
        floorplan_name = fp_json.get("floorplan_name", "")
        floorplan_image = fp_json.get("image", "")

        # Parse size as integer, default to 0 if invalid
        try:
            size = int(sqft) if sqft else 0
        except (ValueError, TypeError):
            size = 0

        # Create floorplan type from beds/baths
        floorplan_type = f"{beds} bed, {baths} bath" if beds and baths else ""

        # Process each unit in query_response
        query_response = fp_json.get("query_response", [])
        if not isinstance(query_response, list):
            return units

        current_timestamp = get_current_timestamp()

        for unit_data in query_response:
            if not isinstance(unit_data, dict):
                continue

            try:
                # Extract unit information
                unit_name = unit_data.get("the_title", "")
                available_date_raw = unit_data.get("ra_date_available", "")
                rent_str = unit_data.get("ra_rent", "")
                apply_url = unit_data.get("apply_url", "")

                # Parse and format availability date
                available_date = parse_availability_date(available_date_raw)

                # Parse rent as integer
                try:
                    rent = int(float(rent_str)) if rent_str else 0
                except (ValueError, TypeError):
                    rent = 0

                # Create price info
                price_info = PriceInfo(
                    price=rent, price_range="", date_fetched=current_timestamp
                )

                # Create unit info
                unit_info = UnitInfo(
                    unit=unit_name,
                    building=building,
                    size=size,
                    available_date=available_date,
                    floorplan_type=floorplan_type,
                    floorplan_link=floorplan_image,
                    floorplan_note=f"Floorplan: {floorplan_name}",
                    prices=[price_info],
                )

                units.append(unit_info)

            except Exception as e:
                logger.error(f"Error parsing unit data: {e}")
                continue

    except Exception as e:
        logger.error(f"Error parsing floorplan JSON: {e}")

    return units


def get_ajax_response_json(driver, fp_div, check_rounds=10, check_interval=0.5):
    """
    Clicks the given floorplan div, waits for the admin-ajax.php response,
    and returns the parsed JSON response as a list.
    """

    # Clear logs before click to avoid stale entries
    driver.get_log("performance")

    url_keyword = "admin-ajax.php"
    fp_div.click()
    found_ajax = False
    ajax_response_body = None

    # Wait for the ajax request to complete and capture its response
    for _ in range(check_rounds):
        logs = driver.get_log("performance")
        for entry in logs:
            try:
                message = json.loads(entry["message"])["message"]
                if not (
                    message["method"] == "Network.responseReceived"
                    and url_keyword in message["params"]["response"]["url"]
                ):
                    continue

                request_id = message["params"]["requestId"]
                response_body = driver.execute_cdp_cmd(
                    "Network.getResponseBody", {"requestId": request_id}
                )
                ajax_response_body = response_body.get("body", "")
                found_ajax = True

            except Exception as e:
                logger.error(f"Error getting response body: {e}")
                continue

        if found_ajax:
            break
        else:
            time.sleep(check_interval)

    # Click outside of the fp_div to close any open overlays or modals
    driver.execute_script("document.elementFromPoint(0, 0).click();")

    if ajax_response_body:
        try:
            return json.loads(ajax_response_body)
        except Exception as e:
            logger.error(f"Error parsing ajax response body as JSON: {e}")
            return []
    return []
