"""Crawl result models."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import orjson


@dataclass
class CrawlResult:
    """Result of a crawl operation."""
    
    url: str
    final_url: str = ""
    status_code: int = 0
    title: str = ""
    
    # Content
    markdown: str = ""
    html: str = ""
    text: str = ""
    
    # Structured data (from domain parsers)
    structured: dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)
    
    # Vietnamese NLP enrichment
    entities: list[dict[str, str]] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    language: str = "vi"
    
    # Chunks (for RAG)
    chunks: list[dict[str, Any]] = field(default_factory=list)
    
    # Parser info
    parser_used: str = "auto"
    content_type: str = ""  # legal, news, realestate, finance, generic
    
    # Performance
    crawl_time_ms: int = 0
    rendered_js: bool = False
    
    # Errors
    error: str | None = None
    
    @property
    def success(self) -> bool:
        return self.error is None and self.status_code in range(200, 400)
    
    @property
    def content_length(self) -> int:
        return len(self.markdown or self.text or "")
    
    def to_dict(self) -> dict:
        """Convert to dict, excluding empty fields."""
        d = {}
        for k, v in self.__dict__.items():
            if v is None or v == "" or v == [] or v == {} or v == 0:
                continue
            d[k] = v
        return d
    
    def to_json(self, pretty: bool = False) -> bytes:
        """Convert to JSON bytes."""
        opt = orjson.OPT_INDENT_2 if pretty else 0
        return orjson.dumps(self.to_dict(), option=opt)
    
    def to_jsonl_rows(self) -> list[bytes]:
        """Convert chunks to JSONL rows for RAG."""
        if not self.chunks:
            return [self.to_json()]
        rows = []
        for chunk in self.chunks:
            row = {
                "url": self.url,
                "title": self.title,
                "content_type": self.content_type,
                **chunk,
            }
            rows.append(orjson.dumps(row))
        return rows
