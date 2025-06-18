"""Scraper for 1 Grove building."""

import re

from bs4 import BeautifulSoup
from loguru import logger
from selenium.webdriver.common.by import By

from jcleasing.models.units import PriceInfo, UnitInfo
from jcleasing.scrapers.base import BaseScraper
from jcleasing.utils.helpers import get_current_timestamp, wait


class GroveScraper(BaseScraper):
    """Scraper for 1 Grove building."""

    def get_units(self):
        """Get all available units from 1 Grove."""
        self.driver.get("https://onegrovejc.com/floorplans/")
        wait()

        # Click the Floorplans tab using aria-controls
        floorplans_tab = self.driver.find_element(
            by=By.CSS_SELECTOR, value="a[aria-controls='Floorplans']"
        )
        floorplans_tab.click()
        wait()

        # Get the innerHTML of the floorplan body
        floorplan_body = self.driver.find_element(by=By.ID, value="jd-fp-body")
        html_content = floorplan_body.get_attribute("innerHTML")

        # Parse with BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")

        # Get all floorplan cards
        floorplan_cards = soup.select(".jd-fp-floorplan-card")

        units = []
        for card in floorplan_cards:
            try:
                # Extract floorplan information
                title = card.select_one(".jd-fp-card-info__title").text.strip()

                # Extract bedroom, bathroom, and size information
                # Collect all span texts inside the info paragraph
                spans = card.select("p.jd-fp-card-info__text span")
                if len(spans) < 3:
                    logger.warning(f"Not enough spans found for floorplan {title}")
                    continue

                bedroom = spans[0].get_text(strip=True)
                bath = spans[1].get_text(strip=True)
                size_text = spans[2].get_text(strip=True)

                # Extract size number from the third span, or fallback to image alt text
                size_match = re.search(r"(\d+)", size_text.replace(",", ""))
                size = None

                if size_match:
                    size = int(size_match.group(1))
                else:
                    # If third span doesn't contain size (e.g., "Den"), try image alt text
                    img_element = card.select_one("img")
                    if img_element:
                        alt_text = img_element.get("alt", "")
                        title_text = img_element.get("title", "")

                        # Try to extract size from alt or title text
                        for text in [alt_text, title_text]:
                            size_match = re.search(r"(\d+)\s*square feet", text)
                            if size_match:
                                size = int(size_match.group(1))
                                break

                if not size:
                    logger.warning(
                        f"Could not parse size for floorplan {title} - skipping"
                    )
                    continue

                # Extract price information
                price_element = card.select_one(".jd-fp-strong-text")
                price_text = (
                    price_element.text.strip() if price_element else "Contact Us"
                )

                # Parse price - handle different price formats
                price = None
                if "Contact Us" not in price_text:
                    # Try to extract price if it's not "Contact Us"
                    if "Base Rent $" in price_text:
                        try:
                            # Remove commas and Base Rent prefix
                            price_str = price_text.replace("Base Rent $", "").replace(
                                ",", ""
                            )
                            price = int(price_str)
                        except ValueError:
                            logger.warning(
                                f"Could not parse price '{price_text}' for floorplan {title}"
                            )
                    else:
                        # Try to extract any dollar amount
                        price_match = re.search(
                            r"\$?([\d,]+)", price_text.replace("$", "")
                        )
                        if price_match:
                            try:
                                price = int(price_match.group(1).replace(",", ""))
                            except ValueError:
                                logger.warning(
                                    f"Could not parse price '{price_text}' for floorplan {title}"
                                )

                # Extract floorplan link from href attribute
                floorplan_link = card.get("href", "")
                if floorplan_link and not floorplan_link.startswith("http"):
                    floorplan_link = f"https://onegrovejc.com{floorplan_link}"

                # Build floorplan note - handle "Den" case
                note_parts = [bedroom, bath]
                if "Den" in size_text:
                    note_parts.append(size_text)  # Add "Den" to the note
                floorplan_note = " | ".join(note_parts)

                # Create UnitInfo
                units.append(
                    UnitInfo(
                        unit="",  # No specific unit number available
                        building="1 Grove",
                        size=size,
                        available_date="1900-01-01",  # No specific available date
                        floorplan_type=title,
                        floorplan_link=floorplan_link,
                        floorplan_note=floorplan_note,
                        prices=[
                            PriceInfo(
                                price=price,
                                price_range=price_text if price is None else "",
                                date_fetched=get_current_timestamp(),
                            )
                        ],
                    )
                )
            except Exception as e:
                logger.warning(f"Error parsing floorplan card: {e}")
                continue

        logger.info(f"Found {len(units)} floorplans")
        return units
