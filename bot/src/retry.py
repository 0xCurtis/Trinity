import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import TypeVar

import requests

logger = logging.getLogger(__name__)

T = TypeVar("T")


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    retriable_statuses: tuple[int, ...] = (429, 500, 502, 503, 504),
    retriable_exceptions: tuple[type[Exception], ...] = (
        requests.RequestException,
        requests.ConnectionError,
        requests.Timeout,
    ),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator that retries a function with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        exponential_base: Base for exponential backoff
        retriable_statuses: HTTP status codes that trigger a retry
        retriable_exceptions: Exception types that trigger a retry
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception: Exception | None = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retriable_exceptions as e:
                    last_exception = e

                    if attempt == max_retries:
                        logger.warning(f"Max retries ({max_retries}) reached for {func.__name__}")
                        raise

                    delay = min(base_delay * (exponential_base**attempt), max_delay)

                    if isinstance(e, requests.HTTPError):
                        status_code = e.response.status_code if e.response else 0
                        if status_code not in retriable_statuses:
                            logger.warning(
                                f"Non-retriable HTTP error {status_code} for {func.__name__}"
                            )
                            raise

                    logger.info(
                        f"Retry {attempt + 1}/{max_retries} for {func.__name__} "
                        f"after {delay:.1f}s: {type(e).__name__}: {e}"
                    )
                    time.sleep(delay)

            raise last_exception

        return wrapper

    return decorator


def is_retriable_error(response: requests.Response) -> bool:
    """Check if an HTTP response indicates a retriable error."""
    return response.status_code in (429, 500, 502, 503, 504)


def check_rate_limit(response: requests.Response) -> int | None:
    """Check for rate limit headers and return retry-after if present.

    Returns:
        Retry-after seconds if rate limited, None otherwise
    """
    if response.status_code == 429:
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return int(retry_after)
            except ValueError:
                pass
    return None
