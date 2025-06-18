from jcleasing.scrapers.grand import Grand235Scraper


class Park18Scraper(Grand235Scraper):
    """Scraper for 235 Grand building."""

    base = "https://www.18park.com"
    floorplan_types = [
        "studio",
        "1-bed-1-bath",
        "2-bed-2-bath",
    ]
