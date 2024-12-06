"""Performance monitoring utilities."""

import time
import logging
import functools
from typing import Any, Callable, TypeVar, cast
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

T = TypeVar('T')

@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""
    function_name: str
    start_time: datetime
    end_time: datetime
    duration: timedelta
    success: bool
    error: Exception | None = None

def measure_performance(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to measure function performance."""
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        start_time = datetime.now()
        start = time.perf_counter()
        error = None
        success = True
        
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            error = e
            success = False
            raise
        finally:
            end_time = datetime.now()
            duration = time.perf_counter() - start
            
            metrics = PerformanceMetrics(
                function_name=func.__name__,
                start_time=start_time,
                end_time=end_time,
                duration=timedelta(seconds=duration),
                success=success,
                error=error
            )
            
            log_performance_metrics(metrics)
    
    return cast(Callable[..., T], wrapper)

def log_performance_metrics(metrics: PerformanceMetrics) -> None:
    """Log performance metrics."""
    status = "succeeded" if metrics.success else "failed"
    logger.info(
        f"{metrics.function_name} {status} - "
        f"Duration: {metrics.duration.total_seconds():.2f}s - "
        f"Started: {metrics.start_time.isoformat()} - "
        f"Ended: {metrics.end_time.isoformat()}"
    )
    
    if not metrics.success and metrics.error:
        logger.error(
            f"{metrics.function_name} failed with error: {str(metrics.error)}"
        ) 