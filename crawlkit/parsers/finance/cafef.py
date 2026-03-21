"""
Parser for cafef.vn — Vietnam's popular financial news and stock data site.

Extracts:
- Financial news articles
- Stock data mentions
- Company information
"""

from __future__ import annotations
import re
from typing import Any
from bs4 import BeautifulSoup

from ..base import BaseParser


class CafeFParser(BaseParser):
    name = "cafef"
    domain = "cafef.vn"
    
    def parse(self, html: str, url: str = "", text: str = "") -> dict[str, Any]:
        """Parse a CafeF article or stock page."""
        soup = BeautifulSoup(html, "lxml")
        
        result = {
            "source": "cafef",
            "url": url,
        }
        
        # Title
        title_el = soup.select_one("h1, .title-detail")
        result["title"] = title_el.get_text(strip=True) if title_el else ""
        
        # Date
        date_el = soup.select_one(".dateandcat, .date, .time-detail")
        if date_el:
            date_text = date_el.get_text(strip=True)
            result["date"] = date_text
            m = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', date_text)
            if m:
                result["date_iso"] = f"{m.group(3)}-{m.group(2).zfill(2)}-{m.group(1).zfill(2)}"
        
        # Article body
        body_el = soup.select_one(".detail-content, .contentdetail, .knc-content")
        if body_el:
            paragraphs = []
            for p in body_el.find_all(["p", "h2", "h3"]):
                t = p.get_text(strip=True)
                if t and len(t) > 10:
                    paragraphs.append(t)
            result["content"] = "\n\n".join(paragraphs)
            result["content_length"] = len(result["content"])
        
        # Extract stock symbols mentioned
        content = result.get("content", "")
        stock_pattern = re.compile(r'\b([A-Z]{3})\b')
        # Common VN stock symbols are 3 uppercase letters
        potential_stocks = stock_pattern.findall(content)
        # Filter out common non-stock words
        noise = {"VND", "USD", "EUR", "GDP", "CEO", "CPI", "FDI", "IPO", "M&A", "ETF"}
        result["stock_mentions"] = list(set(s for s in potential_stocks if s not in noise))
        
        # Category
        breadcrumb = soup.select(".breadcrumb a")
        if breadcrumb:
            result["category"] = breadcrumb[-1].get_text(strip=True)
        
        # Tags
        tags = soup.select(".tags a, .tag-item a")
        result["tags"] = [t.get_text(strip=True) for t in tags]
        
        return result
