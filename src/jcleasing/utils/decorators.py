"""Decorators for the jcleasing package."""
from functools import wraps
from loguru import logger


def exception_helper(func):
    """Decorator to handle exceptions and log them.
    
    Args:
        func: The function to wrap.
        
    Returns:
        The wrapped function with exception handling.
    """
    @wraps(func)
    def wrapped(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"{func} failed at ({args}, {kwargs}), err: {e}")
            return None
    return wrapped
