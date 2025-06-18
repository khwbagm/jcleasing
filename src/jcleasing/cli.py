"""Command line interface for the jcleasing package."""

import argparse
import sys
from typing import List, Optional

from loguru import logger

from jcleasing.core.runner import ScrapingRunner
from jcleasing.core.registry import ScraperRegistry


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        description="JC Leasing scraper - scrape apartment availability data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Run all scrapers
  %(prog)s --debug                   # Run with browser visible
  %(prog)s --scrapers columbus579 haus25  # Run specific scrapers
  %(prog)s --list-scrapers           # List available scrapers
  %(prog)s --output-dir ./results    # Save to custom directory
        """,
    )

    parser.add_argument(
        "--debug", action="store_true", help="Run in debug mode (shows browser)"
    )

    parser.add_argument(
        "--output-dir", default="results", help="Directory to save results (default: data)"
    )

    parser.add_argument(
        "--scrapers", nargs="*", help="Specific scrapers to run (default: all)"
    )

    parser.add_argument(
        "--list-scrapers", action="store_true", help="List available scrapers and exit"
    )

    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save results to file (useful for testing)",
    )

    return parser


def list_scrapers():
    """List all available scrapers."""
    registry = ScraperRegistry()
    scrapers = registry.list_names()

    print("Available scrapers:")
    for scraper in sorted(scrapers):
        print(f"  {scraper}")

    print(f"\nTotal: {len(scrapers)} scrapers")


def main(args: Optional[List[str]] = None):
    """Main CLI entry point.

    Args:
        args: Command line arguments. If None, uses sys.argv.
    """
    parser = create_parser()
    parsed_args = parser.parse_args(args)

    # Handle list-scrapers command
    if parsed_args.list_scrapers:
        list_scrapers()
        return

    # Create runner
    runner = ScrapingRunner(debug=parsed_args.debug, output_dir=parsed_args.output_dir)

    # Run scrapers
    try:
        if parsed_args.no_save:
            results = runner.run(parsed_args.scrapers)
            logger.info(f"Completed scraping. Found data for {len(results)} buildings.")
            for building, units in results.items():
                logger.info(f"  {building}: {len(units)} units")
        else:
            output_file = runner.run_and_save(parsed_args.scrapers)
            logger.info(f"Scraping complete. Results saved to: {output_file}")

    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during scraping: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
