"""
Retry mechanism for API calls with exponential backoff.
"""

import time
import logging
from functools import wraps
from typing import Callable, Any, Tuple, Type

logger = logging.getLogger(__name__)


def retry_on_failure(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Callable[[int, Exception], None] = None
):
    """
    Decorator to retry a function call with exponential backoff on failure.

    Args:
        max_attempts: Maximum number of attempts (default: 3)
        initial_delay: Initial delay in seconds before first retry (default: 1.0)
        backoff_factor: Multiplier for delay after each retry (default: 2.0)
        exceptions: Tuple of exception types to catch and retry (default: all exceptions)
        on_retry: Optional callback function called on each retry with (attempt_number, exception)

    Example:
        @retry_on_failure(max_attempts=3, initial_delay=2.0)
        def fetch_data():
            return api.get_data()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_attempts:
                        logger.error(
                            f"❌ Failed after {max_attempts} attempts: {func.__name__}() - {str(e)}"
                        )
                        raise

                    logger.warning(
                        f"⚠️  Attempt {attempt}/{max_attempts} failed for {func.__name__}(): {str(e)}"
                    )
                    logger.info(f"   Retrying in {delay:.1f} seconds...")

                    # Call the on_retry callback if provided
                    if on_retry:
                        try:
                            on_retry(attempt, e)
                        except Exception as callback_error:
                            logger.error(f"Error in retry callback: {callback_error}")

                    time.sleep(delay)
                    delay *= backoff_factor

            # Should never reach here, but just in case
            if last_exception:
                raise last_exception

        return wrapper
    return decorator


def retry_with_timeout(
    max_attempts: int = 3,
    timeout: float = 30.0,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorator to retry a function call with a maximum total timeout.

    Args:
        max_attempts: Maximum number of attempts (default: 3)
        timeout: Maximum total time in seconds for all attempts (default: 30.0)
        initial_delay: Initial delay in seconds before first retry (default: 1.0)
        backoff_factor: Multiplier for delay after each retry (default: 2.0)
        exceptions: Tuple of exception types to catch and retry (default: all exceptions)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            delay = initial_delay
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                elapsed = time.time() - start_time

                if elapsed >= timeout:
                    logger.error(f"❌ Timeout reached ({timeout}s) for {func.__name__}()")
                    if last_exception:
                        raise last_exception
                    raise TimeoutError(f"Total timeout of {timeout}s exceeded")

                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_attempts:
                        logger.error(
                            f"❌ Failed after {max_attempts} attempts: {func.__name__}() - {str(e)}"
                        )
                        raise

                    # Check if we have time for another attempt
                    if elapsed + delay >= timeout:
                        logger.error(f"❌ No time left for retry (timeout: {timeout}s)")
                        raise

                    logger.warning(
                        f"⚠️  Attempt {attempt}/{max_attempts} failed for {func.__name__}(): {str(e)}"
                    )
                    logger.info(f"   Retrying in {delay:.1f} seconds...")

                    time.sleep(delay)
                    delay *= backoff_factor

            # Should never reach here, but just in case
            if last_exception:
                raise last_exception

        return wrapper
    return decorator


class ConnectionManager:
    """
    Manager for handling connection state and retry logic.
    """

    def __init__(self):
        self.connection_failures = 0
        self.last_failure_time = None
        self.is_connected = True

    def record_failure(self):
        """Record a connection failure"""
        self.connection_failures += 1
        self.last_failure_time = time.time()
        self.is_connected = False
        logger.warning(f"Connection failure recorded (total: {self.connection_failures})")

    def record_success(self):
        """Record a successful connection"""
        if not self.is_connected:
            logger.info("✅ Connection restored")
        self.connection_failures = 0
        self.last_failure_time = None
        self.is_connected = True

    def should_retry(self, max_failures: int = 5) -> bool:
        """Check if we should retry based on failure count"""
        return self.connection_failures < max_failures

    def get_wait_time(self, base_wait: float = 5.0, max_wait: float = 300.0) -> float:
        """Calculate wait time with exponential backoff"""
        if self.connection_failures == 0:
            return 0

        wait_time = base_wait * (2 ** (self.connection_failures - 1))
        return min(wait_time, max_wait)
