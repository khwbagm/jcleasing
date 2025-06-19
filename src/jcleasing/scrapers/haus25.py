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

from jcleasing.utils.basics import parse_availability_date
from jcleasing.models.units import UnitInfo, PriceInfo
from jcleasing.scrapers.base import BaseScraper
from jcleasing.utils.helpers import wait, get_current_timestamp


class Haus25Scraper(BaseScraper):
    """Scraper for Haus25 building."""

    def _get_all_floorplans(self):
        """Get all floorplan elements from the modal."""
        logger.info("Navigating to Haus25 website and opening floorplans modal")

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
            logger.debug("Found the view-all-modal-content div")
        except Exception as e:
            logger.error(
                f"Could not find the view-all-modal-content div: {str(e)}",
                exc_info=True,
            )
            return []

        # Find all <div> elements with class containing "display-floorplan-details" inside modal_content_div
        floorplan_details_divs = modal_content_div.find_elements(
            By.XPATH, ".//div[contains(@class, 'display-floorplan-details')]"
        )

        logger.info(f"Found {len(floorplan_details_divs)} floorplan sections")
        return floorplan_details_divs

    def get_units(self) -> List[UnitInfo]:
        """Retrieve all available units from Haus25 building."""
        units: List[UnitInfo] = []

        logger.info("Starting Haus25 unit scraping")

        # Get initial count of floorplans
        floorplan_divs = self._get_all_floorplans()
        total_floorplans = len(floorplan_divs)
        logger.info(f"Found {total_floorplans} floorplan sections")

        for i in range(total_floorplans):
            logger.info(f"Processing floorplan {i + 1}/{total_floorplans}")

            try:
                # Re-find floorplan elements each time to avoid stale references
                current_floorplan_divs = self._get_floorplan_elements()

                if i >= len(current_floorplan_divs):
                    logger.warning(f"Floorplan {i + 1} not found, skipping")
                    continue

                fp_div = current_floorplan_divs[i]
                fp_json = get_ajax_response_json(self.driver, fp_div)
                parsed_units = parse_fp_json(fp_json)
                units.extend(parsed_units)
                logger.debug(
                    f"Successfully parsed {len(parsed_units)} units from floorplan {i + 1}"
                )

            except Exception as e:
                logger.error(
                    f"Error processing floorplan {i + 1}: {str(e)}", exc_info=True
                )

        logger.info(f"Found {len(units)} units in total")
        return units

    def _get_floorplan_elements(self):
        """Get fresh floorplan elements to avoid stale references."""
        try:
            # Find the modal content div
            modal_content_div = self.driver.find_element(
                By.CSS_SELECTOR, "div.wp-block-group.view-all-modal-content"
            )

            # Find all floorplan detail divs
            floorplan_details_divs = modal_content_div.find_elements(
                By.XPATH, ".//div[contains(@class, 'display-floorplan-details')]"
            )

            logger.debug(f"Re-found {len(floorplan_details_divs)} floorplan elements")
            return floorplan_details_divs

        except Exception as e:
            logger.error(
                f"Error re-finding floorplan elements: {str(e)}", exc_info=True
            )
            return []


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
        logger.debug("Parsing floorplan JSON data")

        # Debug: Log the keys and basic structure of the response
        logger.debug(
            f"AJAX response keys: {list(fp_json.keys()) if fp_json else 'Empty response'}"
        )
        if fp_json:
            logger.debug(f"AJAX response sample: {str(fp_json)[:500]}...")

        # Check if this is just a success message without actual floorplan data
        if not fp_json or set(fp_json.keys()) == {"success", "msg"}:
            logger.debug("Response contains only success message, no floorplan data")
            return units

        # Check if we have the required floorplan fields
        required_fields = [
            "property_title",
            "beds",
            "baths",
            "sqft",
            "floorplan_name",
            "query_response",
        ]
        missing_fields = [field for field in required_fields if field not in fp_json]

        if missing_fields:
            logger.warning(f"Missing required fields in response: {missing_fields}")
            return units

        # Extract basic property information
        building = fp_json.get("property_title", "")
        beds = fp_json.get("beds", "")
        baths = fp_json.get("baths", "")
        sqft = fp_json.get("sqft", "")
        floorplan_name = fp_json.get("floorplan_name", "")
        floorplan_image = fp_json.get("image", "")

        logger.debug(
            f"Processing floorplan: {floorplan_name} ({beds} bed, {baths} bath, {sqft} sqft)"
        )

        # Parse size as integer, default to 0 if invalid
        try:
            size = int(sqft) if sqft else 0
        except (ValueError, TypeError):
            size = 0

        # Create floorplan type from beds/baths
        floorplan_type = f"{beds} bed, {baths} bath" if beds and baths else ""

        # Process each unit in query_response
        query_response = fp_json.get("query_response", [])
        logger.debug(
            f"Query response type: {type(query_response)}, length: {len(query_response) if isinstance(query_response, list) else 'N/A'}"
        )

        if not isinstance(query_response, list):
            logger.warning("query_response is not a list, skipping floorplan")
            return units

        if len(query_response) == 0:
            logger.debug("No units found in query_response for this floorplan")
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

                logger.debug(f"Parsing unit: {unit_name}")

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
                logger.debug(f"Successfully parsed unit: {unit_name}")

            except Exception as e:
                logger.error(
                    f"Error parsing unit data for {unit_data.get('the_title', 'unknown')}: {str(e)}",
                    exc_info=True,
                )
                continue

    except Exception as e:
        logger.error(f"Error parsing floorplan JSON: {str(e)}", exc_info=True)

    return units


def get_ajax_response_json(driver, fp_div, check_rounds=10, check_interval=0.5):
    """
    Clicks the given floorplan div, waits for the admin-ajax.php response,
    and returns the parsed JSON response as a list.
    """
    logger.debug("Clicking floorplan div and capturing AJAX response")

    # Clear logs before click to avoid stale entries
    driver.get_log("performance")

    url_keyword = "admin-ajax.php"
    fp_div.click()
    found_ajax = False
    ajax_responses = []  # Collect all responses

    # Wait for the ajax request to complete and capture its response
    for round_num in range(check_rounds):
        logs = driver.get_log("performance")
        logger.debug(
            f"Round {round_num + 1}: Found {len(logs)} performance log entries"
        )

        for entry in logs:
            try:
                message = json.loads(entry["message"])["message"]
                if not (
                    message["method"] == "Network.responseReceived"
                    and url_keyword in message["params"]["response"]["url"]
                ):
                    continue

                logger.debug(
                    f"Found AJAX response URL: {message['params']['response']['url']}"
                )
                request_id = message["params"]["requestId"]
                response_body = driver.execute_cdp_cmd(
                    "Network.getResponseBody", {"requestId": request_id}
                )
                response_text = response_body.get("body", "")

                if response_text:
                    ajax_responses.append(response_text)
                    found_ajax = True
                    logger.debug(f"Successfully captured AJAX response")
                    logger.debug(f"Response body length: {len(response_text)}")

            except Exception as e:
                logger.error(f"Error getting response body: {str(e)}", exc_info=True)
                continue

        if found_ajax:
            break
        else:
            time.sleep(check_interval)

    if not found_ajax:
        logger.warning(f"AJAX response not found after {check_rounds} rounds")

    # Click outside of the fp_div to close any open overlays or modals
    driver.execute_script("document.elementFromPoint(0, 0).click();")

    # Choose the best response from all collected responses
    best_response = choose_best_ajax_response(ajax_responses)

    if best_response:
        try:
            parsed_json = json.loads(best_response)
            logger.debug(
                f"Successfully parsed JSON response with {len(parsed_json)} top-level keys"
            )
            return parsed_json
        except Exception as e:
            logger.error(
                f"Error parsing ajax response body as JSON: {str(e)}", exc_info=True
            )
            logger.debug(f"Raw response body: {best_response[:200]}...")
            return []

    logger.debug("No valid AJAX response found, returning empty list")
    return []


def choose_best_ajax_response(responses):
    """
    Choose the best AJAX response from a list of responses.
    Prioritizes responses with actual floorplan data over simple success messages.
    """
    if not responses:
        return None

    logger.debug(f"Choosing best response from {len(responses)} AJAX responses")

    # Try to parse each response and score them
    scored_responses = []

    for response in responses:
        try:
            parsed = json.loads(response)
            score = score_ajax_response(parsed)
            scored_responses.append((score, response, parsed))
            logger.debug(f"Response with length {len(response)} scored {score}")
        except:
            # If it can't be parsed as JSON, give it a very low score
            scored_responses.append((0, response, None))

    # Sort by score (highest first) and return the best response
    if scored_responses:
        scored_responses.sort(key=lambda x: x[0], reverse=True)
        best_score, best_response, best_parsed = scored_responses[0]
        logger.debug(
            f"Selected response with score {best_score} and length {len(best_response)}"
        )
        return best_response

    # Fallback to longest response if scoring fails
    longest_response = max(responses, key=len)
    logger.debug(
        f"Fallback: selected longest response with length {len(longest_response)}"
    )
    return longest_response


def score_ajax_response(parsed_response):
    """
    Score an AJAX response based on how likely it is to contain useful floorplan data.
    Higher scores indicate more useful responses.
    """
    if not isinstance(parsed_response, dict):
        return 0

    score = 0

    # Check for floorplan-specific fields
    floorplan_fields = [
        "property_title",
        "beds",
        "baths",
        "sqft",
        "floorplan_name",
        "query_response",
    ]
    for field in floorplan_fields:
        if field in parsed_response:
            score += 10

    # Bonus for having query_response with actual data
    query_response = parsed_response.get("query_response", [])
    if isinstance(query_response, list) and len(query_response) > 0:
        score += 50  # Big bonus for having units

    # Penalty for being just a success message
    if set(parsed_response.keys()) == {"success", "msg"}:
        score = 1  # Very low score, but not zero

    return score
