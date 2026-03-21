"""CrawlKit Python SDK - Web + Video Intelligence API for AI."""

from .client import AsyncCrawlKit, CrawlKit
from .exceptions import (
    AuthenticationError,
    CrawlKitError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)
from .types import ParserInfo, ScrapeResult, UsageStats

__version__ = "0.1.0"
__all__ = [
    "CrawlKit",
    "AsyncCrawlKit",
    "ScrapeResult",
    "ParserInfo",
    "UsageStats",
    "CrawlKitError",
    "AuthenticationError",
    "RateLimitError",
    "NotFoundError",
    "ValidationError",
    "ServerError",
]
