"""Scraper for 1 Grove building."""

import re
from typing import List, Optional

from bs4 import BeautifulSoup
from loguru import logger
from selenium.webdriver.common.by import By

from jcleasing.models.units import PriceInfo, UnitInfo
from jcleasing.scrapers.base import BaseScraper
from jcleasing.utils.helpers import get_current_timestamp, wait


class GroveScraper(BaseScraper):
    """Scraper for 1 Grove building."""

    def get_units(self) -> List[UnitInfo]:
        """Get all available units from 1 Grove."""
        logger.info("Fetching units from 1 Grove")

        try:
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
                    unit_info = self._parse_floorplan_card(card)
                    if unit_info:
                        units.append(unit_info)
                        logger.debug(
                            f"Successfully parsed floorplan: {unit_info.floorplan_type}"
                        )
                except Exception as e:
                    logger.error(
                        f"Error parsing floorplan card: {str(e)}", exc_info=True
                    )

            logger.info(f"Found {len(units)} floorplans")
            return units

        except Exception as e:
            logger.error(f"Error fetching units from 1 Grove: {str(e)}", exc_info=True)
            return []

    def _parse_floorplan_card(self, card) -> Optional[UnitInfo]:
        """Parse unit information from a floorplan card element."""
        logger.debug("Parsing floorplan card")

        # Extract floorplan title
        title = self._extract_title(card)
        if not title:
            logger.warning("Could not extract title from floorplan card")
            return None

        # Extract bedroom, bathroom, and size information
        unit_details = self._extract_unit_details(card)
        if not unit_details:
            logger.warning(f"Could not extract unit details for floorplan {title}")
            return None

        bedroom, bath, size = unit_details

        # Extract price information
        price_info = self._extract_price_info(card, title)

        # Extract floorplan link
        floorplan_link = self._extract_floorplan_link(card)

        # Build floorplan note
        floorplan_note = self._build_floorplan_note(bedroom, bath, card)

        return UnitInfo(
            unit="",  # No specific unit number available
            building="1 Grove",
            size=size,
            available_date="1900-01-01",  # No specific available date
            floorplan_type=title,
            floorplan_link=floorplan_link,
            floorplan_note=floorplan_note,
            prices=[price_info],
        )

    def _extract_title(self, card) -> Optional[str]:
        """Extract the floorplan title from the card."""
        title_element = card.select_one(".jd-fp-card-info__title")
        return title_element.text.strip() if title_element else None

    def _extract_unit_details(self, card) -> Optional[tuple]:
        """Extract bedroom, bathroom, and size information from the card."""
        spans = card.select("p.jd-fp-card-info__text span")
        if len(spans) < 3:
            return None

        bedroom = spans[0].get_text(strip=True)
        bath = spans[1].get_text(strip=True)
        size_text = spans[2].get_text(strip=True)

        # Extract size number from the third span, or fallback to image alt text
        size = self._extract_size(size_text, card)
        if not size:
            return None

        return bedroom, bath, size

    def _extract_size(self, size_text: str, card) -> Optional[int]:
        """Extract size from text or image alt/title attributes."""
        # Try to extract size from the size_text first
        size_match = re.search(r"(\d+)", size_text.replace(",", ""))
        if size_match:
            return int(size_match.group(1))

        # If third span doesn't contain size (e.g., "Den"), try image alt text
        img_element = card.select_one("img")
        if img_element:
            alt_text = img_element.get("alt", "")
            title_text = img_element.get("title", "")

            # Try to extract size from alt or title text
            for text in [alt_text, title_text]:
                size_match = re.search(r"(\d+)\s*square feet", text)
                if size_match:
                    return int(size_match.group(1))

        return None

    def _extract_price_info(self, card, title: str) -> PriceInfo:
        """Extract price information from the card."""
        price_element = card.select_one(".jd-fp-strong-text")
        price_text = price_element.text.strip() if price_element else "Contact Us"

        price = None
        if "Contact Us" not in price_text:
            price = self._parse_price_text(price_text, title)

        return PriceInfo(
            price=price,
            price_range=price_text if price is None else "",
            date_fetched=get_current_timestamp(),
        )

    def _parse_price_text(self, price_text: str, title: str) -> Optional[int]:
        """Parse price from price text."""
        try:
            if "Base Rent $" in price_text:
                # Remove commas and Base Rent prefix
                price_str = price_text.replace("Base Rent $", "").replace(",", "")
                return int(price_str)
            else:
                # Try to extract any dollar amount
                price_match = re.search(r"\$?([\d,]+)", price_text.replace("$", ""))
                if price_match:
                    return int(price_match.group(1).replace(",", ""))
        except ValueError:
            logger.warning(
                f"Could not parse price '{price_text}' for floorplan {title}"
            )

        return None

    def _extract_floorplan_link(self, card) -> str:
        """Extract floorplan link from the card."""
        floorplan_link = card.get("href", "")
        if floorplan_link and not floorplan_link.startswith("http"):
            floorplan_link = f"https://onegrovejc.com/{floorplan_link}"
        return floorplan_link

    def _build_floorplan_note(self, bedroom: str, bath: str, card) -> str:
        """Build the floorplan note from bedroom, bath, and additional info."""
        note_parts = [bedroom, bath]

        # Check if there's a "Den" in the third span
        spans = card.select("p.jd-fp-card-info__text span")
        if len(spans) >= 3:
            size_text = spans[2].get_text(strip=True)
            if "Den" in size_text:
                note_parts.append(size_text)

        return " | ".join(note_parts)
