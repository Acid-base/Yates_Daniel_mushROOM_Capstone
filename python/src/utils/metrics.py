"""Performance monitoring utilities."""

import time
import functools
from typing import Any, Callable
from contextlib import contextmanager

from .logging import get_logger

logger = get_logger(__name__)

@contextmanager
def measure_time(operation_name: str):
    """Context manager to measure operation time."""
    start = time.perf_counter()
    try:
        yield
    finally:
        duration = time.perf_counter() - start
        logger.info(f"{operation_name} took {duration:.2f} seconds")

def measure_performance(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to measure function performance."""
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        with measure_time(func.__name__):
            return await func(*args, **kwargs)
    return wrapper 