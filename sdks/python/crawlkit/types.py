"""Type definitions for CrawlKit SDK."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ScrapeResult:
    """Result from a scrape operation."""
    
    url: str
    title: Optional[str] = None
    content: str = ""
    chunks: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScrapeResult":
        """Create a ScrapeResult from API response."""
        return cls(
            url=data.get("url", ""),
            title=data.get("title"),
            content=data.get("content", ""),
            chunks=data.get("chunks"),
            metadata=data.get("metadata")
        )


@dataclass
class ParserInfo:
    """Information about a parser."""
    
    name: str
    description: str
    supported_domains: Optional[List[str]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ParserInfo":
        """Create ParserInfo from API response."""
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            supported_domains=data.get("supported_domains")
        )


@dataclass
class UsageStats:
    """API usage statistics."""
    
    requests_used: int
    requests_limit: int
    requests_remaining: int
    reset_at: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UsageStats":
        """Create UsageStats from API response."""
        return cls(
            requests_used=data.get("requests_used", 0),
            requests_limit=data.get("requests_limit", 0),
            requests_remaining=data.get("requests_remaining", 0),
            reset_at=data.get("reset_at")
        )
