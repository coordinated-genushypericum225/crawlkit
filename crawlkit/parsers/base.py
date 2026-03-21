"""Base parser interface."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseParser(ABC):
    """Base class for domain-specific parsers."""
    
    name: str = "base"
    domain: str = ""
    
    @abstractmethod
    def parse(self, html: str, url: str = "", text: str = "") -> dict[str, Any]:
        """
        Parse HTML into structured data.
        
        Args:
            html: Full page HTML
            url: Page URL
            text: Pre-extracted text (optional)
        
        Returns:
            Dict with domain-specific structured fields
        """
        ...
    
    def discover(self, query: Optional[str] = None, limit: int = 100) -> list[dict]:
        """
        Discover URLs from this source.
        Override in subclasses that support discovery.
        """
        raise NotImplementedError(f"{self.name} doesn't support discovery")
    
    def can_parse(self, url: str) -> bool:
        """Check if this parser can handle the given URL."""
        from urllib.parse import urlparse
        return self.domain in urlparse(url).netloc.lower()
