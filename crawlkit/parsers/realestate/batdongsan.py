"""
Parser for batdongsan.com.vn — Vietnam's largest real estate platform.

Extracts:
- Property title, price, area, location
- Property details (rooms, floors, direction, etc.)
- Description
- Contact info
- Listing metadata
"""

from __future__ import annotations
import re
from typing import Any
from bs4 import BeautifulSoup

from ..base import BaseParser


class BatDongSanParser(BaseParser):
    name = "batdongsan"
    domain = "batdongsan.com.vn"
    
    def parse(self, html: str, url: str = "", text: str = "") -> dict[str, Any]:
        """Parse a BatDongSan listing page."""
        soup = BeautifulSoup(html, "lxml")
        
        result = {
            "source": "batdongsan",
            "url": url,
        }
        
        # Title
        title_el = soup.select_one("h1, .re__pr-title")
        result["title"] = title_el.get_text(strip=True) if title_el else ""
        
        # Price
        price_el = soup.select_one(".re__pr-short-info-item--price, .price, .js__pr-price")
        if price_el:
            price_text = price_el.get_text(strip=True)
            result["price_text"] = price_text
            result["price"] = self._parse_price(price_text)
        
        # Area
        area_el = soup.select_one(".re__pr-short-info-item--acreage, .area, .js__pr-acreage")
        if area_el:
            area_text = area_el.get_text(strip=True)
            result["area_text"] = area_text
            m = re.search(r'([\d,.]+)\s*m', area_text)
            if m:
                result["area_m2"] = float(m.group(1).replace(",", "."))
        
        # Location
        location_el = soup.select_one(".re__pr-short-info-item--address, .address, .js__pr-address")
        result["location"] = location_el.get_text(strip=True) if location_el else ""
        
        # Property details
        details = {}
        for item in soup.select(".re__pr-specs-content-item, .info-attr li, .detail-info li"):
            label_el = item.select_one(".title, .name, dt, span:first-child")
            value_el = item.select_one(".value, .content, dd, span:last-child")
            if label_el and value_el:
                key = label_el.get_text(strip=True).lower()
                val = value_el.get_text(strip=True)
                
                if "phòng ngủ" in key:
                    details["bedrooms"] = val
                elif "phòng tắm" in key or "toilet" in key:
                    details["bathrooms"] = val
                elif "tầng" in key and "số" in key:
                    details["floors"] = val
                elif "hướng" in key and "nhà" in key:
                    details["direction"] = val
                elif "pháp lý" in key:
                    details["legal_status"] = val
                elif "nội thất" in key:
                    details["furniture"] = val
                elif "loại" in key:
                    details["property_type"] = val
        
        result["details"] = details
        
        # Description
        desc_el = soup.select_one(".re__pr-description .re__section-body, .detail-content, .pr-info-content")
        result["description"] = desc_el.get_text(separator="\n", strip=True) if desc_el else ""
        
        # Contact
        contact_el = soup.select_one(".re__contact-name, .agent-name, .seller-name")
        if contact_el:
            result["contact_name"] = contact_el.get_text(strip=True)
        
        phone_el = soup.select_one(".re__contact-phone, .phone, [href^='tel:']")
        if phone_el:
            phone = phone_el.get("href", "").replace("tel:", "") or phone_el.get_text(strip=True)
            result["contact_phone"] = phone
        
        # Listing type (bán / cho thuê)
        if "ban-" in url or "bán" in result.get("title", "").lower():
            result["listing_type"] = "sale"
        elif "thue-" in url or "thuê" in result.get("title", "").lower():
            result["listing_type"] = "rent"
        
        result["content_length"] = len(result.get("description", ""))
        
        return result
    
    def _parse_price(self, price_text: str) -> dict:
        """Parse Vietnamese price text to structured format."""
        price = {"raw": price_text}
        
        # Patterns: "3.5 tỷ", "800 triệu", "15 triệu/tháng", "Thỏa thuận"
        if "thỏa thuận" in price_text.lower() or "liên hệ" in price_text.lower():
            price["type"] = "negotiable"
            return price
        
        m = re.search(r'([\d,.]+)\s*(tỷ|triệu|tr|nghìn)', price_text.lower())
        if m:
            value = float(m.group(1).replace(",", "."))
            unit = m.group(2)
            
            if unit == "tỷ":
                price["vnd"] = int(value * 1_000_000_000)
            elif unit in ("triệu", "tr"):
                price["vnd"] = int(value * 1_000_000)
            elif unit == "nghìn":
                price["vnd"] = int(value * 1_000)
            
            price["type"] = "per_month" if "/tháng" in price_text else "total"
        
        return price
