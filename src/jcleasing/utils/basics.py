from loguru import logger
from datetime import datetime


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
        "available",
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
