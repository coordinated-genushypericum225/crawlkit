"""
Parser for vbpl.vn — Government's official legal document database.

Handles:
- ASP.NET ViewState forms
- Long CSS selector IDs (ctl00_PlaceHolderMain_...)
- PostBack-based pagination
"""

from __future__ import annotations
import re
from typing import Any
from bs4 import BeautifulSoup

from ..base import BaseParser


class VBPLParser(BaseParser):
    name = "vbpl"
    domain = "vbpl.vn"
    
    def parse(self, html: str, url: str = "", text: str = "") -> dict[str, Any]:
        """Parse a vbpl.vn legal document page."""
        soup = BeautifulSoup(html, "lxml")
        
        result = {
            "source": "vbpl",
            "url": url,
        }
        
        # Title
        title_tag = soup.find("title")
        result["title"] = title_tag.string.strip() if title_tag and title_tag.string else ""
        
        # Main content - vbpl uses very long ASP.NET IDs
        content_selectors = [
            "#ctl00_PlaceHolderMain_ContentPlaceHolderMain_toanvan",
            "#toanvan",
            ".toanvan",
            ".content-doc",
        ]
        
        content_text = ""
        for sel in content_selectors:
            el = soup.select_one(sel)
            if el:
                content_text = el.get_text(separator="\n", strip=True)
                if len(content_text) > 100:
                    break
        
        result["content"] = content_text
        result["content_length"] = len(content_text)
        
        # Extract metadata from info box
        for row in soup.select("tr, .info-row, .doc-info"):
            cells = row.find_all(["td", "th", "span"])
            if len(cells) >= 2:
                key = cells[0].get_text(strip=True).lower()
                val = cells[1].get_text(strip=True)
                
                if "số hiệu" in key:
                    result["so_hieu"] = val
                elif "loại" in key:
                    result["loai_van_ban"] = val
                elif "hiệu lực" in key and "ngày" not in key:
                    result["tinh_trang"] = val
                elif "ngày" in key and "hiệu lực" in key:
                    result["ngay_hieu_luc"] = val
                elif "ban hành" in key and "ngày" in key:
                    result["ngay_ban_hanh"] = val
                elif "cơ quan" in key:
                    result["co_quan_ban_hanh"] = val
        
        # Extract articles
        articles = []
        dieu_pattern = re.compile(r'Điều\s+(\d+[a-z]?)\.?\s*([^\n]*)', re.MULTILINE)
        for m in dieu_pattern.finditer(content_text):
            articles.append({
                "number": m.group(1),
                "title": m.group(2).strip(),
            })
        
        result["articles"] = articles
        result["articles_count"] = len(articles)
        
        return result
