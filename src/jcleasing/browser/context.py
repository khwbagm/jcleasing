"""WebDriver context management for the jcleasing package."""
from contextlib import contextmanager
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from logzero import logger


class WebDriverContext:
    """Context manager for WebDriver instances with automatic cleanup."""
    
    def __init__(self, debug: bool = False):
        """Initialize the WebDriver context.
        
        Args:
            debug: Whether to run in debug mode (visible browser).
        """
        self.debug = debug
        self.driver = None
    
    def __enter__(self):
        """Enter the context and create a WebDriver instance."""
        options = Options()
        if not self.debug:
            options.add_argument("--headless")
        
        # Set some reasonable defaults
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        try:
            self.driver = webdriver.Firefox(options=options)
            # Set reasonable timeouts
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
            return self.driver
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            if self.driver:
                self.driver.quit()
            raise
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context and clean up the WebDriver."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.error(f"Error while quitting WebDriver: {e}")
        
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
