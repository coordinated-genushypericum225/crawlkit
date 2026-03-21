"""
CrawlKit — Vietnamese Web Intelligence API
Crawl, parse, and structure Vietnamese web data for AI.
"""

__version__ = "0.1.0"

from .core.crawler import CrawlKit
from .core.result import CrawlResult

__all__ = ["CrawlKit", "CrawlResult"]
