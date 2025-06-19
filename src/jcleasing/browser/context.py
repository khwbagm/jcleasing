"""WebDriver context management for the jcleasing package."""

from contextlib import contextmanager
from seleniumbase import Driver
from loguru import logger


class WebDriverContext:
    """Context manager for WebDriver instances with automatic cleanup."""

    def __init__(self, debug: bool = False):
        """Initialize the WebDriver context.

        Args:
            debug: Whether to run in debug mode (visible browser).
        """
        self.debug = debug
        self.driver_manager = None

    def __enter__(self):
        """Enter the context and create a WebDriver instance."""
        try:
            # Use SeleniumBase Driver with UC mode
            self.driver_manager = Driver(
                uc=True,  # Enable undetected mode
                headless=not self.debug,  # Headless unless debug
                log_cdp_events=True,  # Enable CDP logging for AJAX interception
                no_sandbox=True,  # Standard Chrome option
                disable_gpu=False,  # Keep GPU enabled unless needed
            )
            
            # Enable network logging for AJAX interception
            self.driver_manager.execute_cdp_cmd("Network.enable", {})
            
            # Set reasonable timeouts
            self.driver_manager.set_page_load_timeout(30)
            self.driver_manager.implicitly_wait(10)
            
            return self.driver_manager
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            if self.driver_manager:
                try:
                    self.driver_manager.quit()
                except:
                    pass
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context and clean up the WebDriver."""
        if self.driver_manager:
            try:
                self.driver_manager.quit()
            except Exception as e:
                logger.error(f"Error while cleaning up WebDriver: {e}")

        # Don't suppress exceptions
        return False


@contextmanager
def new_driver(debug: bool = False):
    """Create a new WebDriver instance with retry logic.

    This is a convenience function that creates and manages a WebDriverContext.

    Example:
        with new_driver(debug=False) as driver:
            # use driver here
            pass

    Args:
        debug: Whether to run in debug mode (visible browser).

    Yields:
        WebDriver: A new WebDriver instance.
    """
    with WebDriverContext(debug=debug) as driver:
        yield driver
