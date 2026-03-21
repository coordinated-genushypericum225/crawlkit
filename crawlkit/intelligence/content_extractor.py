"""
Adaptive Content Extractor - Universal content extraction engine.

Works on ANY website without site-specific parsers.
Automatically detects content type and extracts structured data.

This is CrawlKit's competitive moat.
"""

from __future__ import annotations
import re
from typing import Any, Optional
from dataclasses import dataclass
from urllib.parse import urlparse
from bs4 import BeautifulSoup, Tag

from .noise_filter import NoiseFilter
from .schema_parser import SchemaParser


@dataclass
class ExtractionResult:
    """Result of adaptive extraction."""
    content_type: str  # article, product, listing, forum, profile, homepage, generic
    title: str
    content: str  # Main content text
    metadata: dict[str, Any]  # Extracted fields (varies by content type)
    confidence: float  # 0.0-1.0 confidence score
    raw_html: str  # Original HTML (optional)


class AdaptiveExtractor:
    """
    Universal content extraction — works on any website without site-specific rules.
    
    Uses multiple signals to detect content type and extract structured data:
    - HTML5 semantic tags (article, main, section)
    - Schema.org / Open Graph metadata
    - Content density scoring
    - Link density analysis
    - Vietnamese-specific patterns
    """
    
    # Content type detection signals
    SIGNALS = {
        "article": {
            "meta": ["article:published_time", "og:type=article", "schema:Article", "schema:NewsArticle", "schema:BlogPosting"],
            "elements": ["article", ".article", ".post", ".post-content", "time", "datetime", ".entry-content"],
            "patterns": ["author", "published", "updated", "min read", "phút đọc", "tác giả", "đăng ngày"],
        },
        "product": {
            "meta": ["og:type=product", "product:price", "schema:Product", "product:availability"],
            "elements": [".price", ".add-to-cart", ".product", "[itemprop=price]", ".buy-button", ".btn-buy"],
            "patterns": [
                r"giá", r"₫", r"đ(?:\s|$)", r"vnđ", r"vnd",  # Vietnamese price
                r"mua ngay", r"thêm vào giỏ", r"add to cart", r"buy now",
                r"còn hàng", r"hết hàng", r"in stock", r"out of stock",
            ],
        },
        "listing": {
            "elements": [".item", ".card", ".listing", "ul > li > a", ".grid-item", ".list-item"],
            "patterns": ["items", "results", "kết quả", "sản phẩm"],
            "heuristic": "3+ sibling elements with similar structure",
        },
        "forum": {
            "elements": [".post", ".reply", ".comment", ".message", ".thread"],
            "patterns": ["replied", "posted", "quote", "trả lời", "đã đăng"],
        }
    }
    
    def __init__(self):
        """Initialize extractor with noise filter and schema parser."""
        self.noise_filter = NoiseFilter()
        self.schema_parser = SchemaParser()
    
    def extract(self, html: str, url: str) -> ExtractionResult:
        """
        Main entry: extract structured content from any HTML page.
        
        Args:
            html: Full page HTML
            url: Page URL
            
        Returns:
            ExtractionResult with detected content type and extracted data
        """
        soup = BeautifulSoup(html, "lxml")
        
        # Extract structured metadata first
        schema_data = self.schema_parser.merge(soup)
        
        # Detect content type
        content_type = self._detect_content_type(soup, url, schema_data)
        
        # Clean noise
        clean_soup = self.noise_filter.clean(soup)
        
        # Find main content area
        main_content = self._find_main_content(clean_soup, soup)
        
        # Extract based on content type
        if content_type == "article":
            result = self._extract_article(soup, main_content, schema_data)
        elif content_type == "product":
            result = self._extract_product(soup, main_content, schema_data)
        elif content_type == "listing":
            result = self._extract_listing(soup, main_content, schema_data)
        elif content_type == "forum":
            result = self._extract_forum(soup, main_content, schema_data)
        else:
            # Generic extraction
            result = self._extract_generic(soup, main_content, schema_data)
        
        # Add source URL and domain
        domain = urlparse(url).netloc.replace("www.", "")
        result["url"] = url
        result["source"] = domain
        
        # Calculate confidence score
        confidence = self._calculate_confidence(content_type, result, schema_data)
        
        # Build content text
        content_text = self._build_content_text(result, content_type)
        
        return ExtractionResult(
            content_type=content_type,
            title=result.get("title", ""),
            content=content_text,
            metadata=result,
            confidence=confidence,
            raw_html=str(main_content) if main_content else "",
        )
    
    def _detect_content_type(self, soup: BeautifulSoup, url: str, schema_data: dict) -> str:
        """
        Detect page type: article, product, listing, forum, profile, homepage.
        
        Args:
            soup: BeautifulSoup object
            url: Page URL
            schema_data: Structured data from schema parser
            
        Returns:
            Content type string
        """
        scores = {
            "article": 0,
            "product": 0,
            "listing": 0,
            "forum": 0,
        }
        
        # Check schema data (strongest signal)
        for content_type, signals in self.SIGNALS.items():
            if "meta" in signals:
                for meta_signal in signals["meta"]:
                    if "=" in meta_signal:
                        # Check for specific value (e.g., "og:type=article")
                        key, value = meta_signal.split("=", 1)
                        if schema_data.get(key.replace(":", "_")) == value:
                            scores[content_type] += 5
                        if schema_data.get("type") == value:
                            scores[content_type] += 5
                    else:
                        # Check for presence of key
                        key = meta_signal.replace(":", "_").replace("schema:", "")
                        if key in schema_data or meta_signal in str(schema_data.get("jsonld", [])):
                            scores[content_type] += 3
        
        # Check HTML elements
        for content_type, signals in self.SIGNALS.items():
            if "elements" in signals:
                for selector in signals["elements"]:
                    try:
                        elements = soup.select(selector) if selector.startswith((".","[","#")) else soup.find_all(selector)
                        if elements:
                            scores[content_type] += len(elements) * 0.5
                    except:
                        pass
        
        # Check text patterns
        page_text = soup.get_text()[:5000].lower()  # First 5000 chars
        
        for content_type, signals in self.SIGNALS.items():
            if "patterns" in signals:
                for pattern in signals["patterns"]:
                    if isinstance(pattern, str):
                        # Simple string match
                        if pattern.lower() in page_text:
                            scores[content_type] += 1
                    else:
                        # Regex pattern
                        if re.search(pattern, page_text, re.IGNORECASE):
                            scores[content_type] += 1
        
        # Check listing heuristic (repeated similar elements)
        if self._has_repeated_structure(soup):
            scores["listing"] += 5
        
        # Return type with highest score
        best_type = max(scores, key=scores.get)
        best_score = scores[best_type]
        
        # Need at least score of 2 to be confident
        return best_type if best_score >= 2 else "generic"
    
    def _has_repeated_structure(self, soup: BeautifulSoup) -> bool:
        """Check if page has 3+ sibling elements with similar structure (listing indicator)."""
        # Look for common listing containers
        containers = soup.select(".items, .grid, .list, .results, .listings, ul, ol")
        
        for container in containers[:10]:  # Check first 10 containers
            children = [c for c in container.children if isinstance(c, Tag)]
            
            if len(children) < 3:
                continue
            
            # Check if first 3 children have similar structure
            first_three = children[:3]
            
            # Compare tag names and class patterns
            tag_names = [c.name for c in first_three]
            class_lists = [tuple(sorted(c.get("class", []))) for c in first_three]
            
            # If all have same tag and similar classes, likely a listing
            if len(set(tag_names)) == 1 and len(set(class_lists)) == 1:
                return True
        
        return False
    
    def _find_main_content(self, clean_soup: BeautifulSoup, original_soup: BeautifulSoup) -> Optional[Tag]:
        """
        Find the main content area using multiple signals.
        
        Args:
            clean_soup: Noise-filtered soup
            original_soup: Original soup (fallback)
            
        Returns:
            Main content Tag or None
        """
        # 1. Try semantic HTML5 tags first
        for selector in ["article", "main", "[role='main']"]:
            element = clean_soup.select_one(selector)
            if element and len(element.get_text(strip=True)) > 100:
                return element
        
        # 2. Try Wikipedia-specific selectors
        for selector in ["#mw-content-text", "#bodyContent", ".mw-parser-output"]:
            element = clean_soup.select_one(selector)
            if element and len(element.get_text(strip=True)) > 100:
                return element
        
        # 3. Score all block elements
        candidates = []
        
        for tag in clean_soup.find_all(["div", "section", "article", "main"]):
            score = self._calculate_content_score(tag)
            
            if score > 0:
                candidates.append((tag, score))
        
        # Sort by score
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Return highest scoring element
        if candidates:
            best_element = candidates[0][0]
            best_text = best_element.get_text(strip=True)
            
            # If extracted content is too short but HTML is large, try broader extraction
            if len(best_text) < 200 and len(str(original_soup)) > 5000:
                # Try to find largest div with content
                body = clean_soup.find("body")
                if body:
                    all_divs = body.find_all("div", recursive=True)
                    
                    # Find div with most text
                    largest_div = max(all_divs, key=lambda d: len(d.get_text(strip=True)), default=None)
                    
                    if largest_div and len(largest_div.get_text(strip=True)) > len(best_text) * 2:
                        return largest_div
            
            return best_element
        
        # 4. Fallback to body
        return clean_soup.find("body") or clean_soup
    
    def _calculate_content_score(self, element: Tag) -> float:
        """
        Score an HTML element for content density.
        
        Higher score = more likely to be main content.
        
        Factors:
        - Text density (text length / total HTML length)
        - Paragraph count
        - Low link density (few links = good for content)
        - Position on page (earlier = better)
        
        Args:
            element: BeautifulSoup Tag
            
        Returns:
            Content score (0.0+, higher is better)
        """
        text = element.get_text(strip=True)
        text_len = len(text)
        
        # Must have some text (lowered threshold from 50 to 25)
        if text_len < 25:
            return 0.0
        
        html_len = len(str(element))
        
        # Text density ratio
        text_density = text_len / html_len if html_len > 0 else 0
        
        # Paragraph count (more paragraphs = more content)
        p_count = len(element.find_all("p"))
        
        # Link density (lower is better for content)
        links = element.find_all("a")
        link_text_len = sum(len(a.get_text(strip=True)) for a in links)
        link_density = link_text_len / text_len if text_len > 0 else 0
        
        # Calculate score
        score = 0.0
        
        # Text density (0-10 points)
        score += text_density * 10
        
        # Paragraph count (0-10 points, cap at 20 paragraphs)
        score += min(p_count / 2, 10)
        
        # Low link density bonus (0-5 points) - but don't penalize too much for Wikipedia-style content
        if link_density < 0.5:  # Raised threshold from 0.3 to 0.5 to be more lenient
            score += (0.5 - link_density) * 10  # Reduced multiplier from 15 to 10
        
        # Length bonus (longer content = more likely to be main)
        if text_len > 500:
            score += 5
        if text_len > 1500:
            score += 5
        if text_len > 3000:
            score += 10  # Big bonus for very long content
        
        # Reduced penalty for shorter blocks (removed the < 200 penalty)
        # This allows Wikipedia-style content with many short paragraphs
        
        return score
    
    def _extract_article(self, soup: BeautifulSoup, main_content: Tag, schema_data: dict) -> dict:
        """Extract article-specific fields."""
        result = {}
        
        # Title: h1, og:title, schema, <title>
        result["title"] = (
            schema_data.get("title") or
            schema_data.get("headline") or
            self._find_text(soup, "h1") or
            self._find_text(soup, "title") or
            ""
        )
        
        # Author
        result["author"] = (
            schema_data.get("author") or
            self._find_text(soup, ".author, .byline, [rel='author'], [itemprop='author']") or
            ""
        )
        
        # Dates
        result["published_date"] = self._extract_date(soup, schema_data, "published")
        result["modified_date"] = self._extract_date(soup, schema_data, "modified")
        
        # Category/Section
        result["category"] = self._extract_category(soup)
        
        # Tags
        result["tags"] = self._extract_tags(soup, schema_data)
        
        # Summary/Description
        result["summary"] = (
            schema_data.get("description") or
            self._find_text(soup, ".summary, .lead, .sapo, .description") or
            self._get_first_paragraph(main_content) or
            ""
        )
        
        # Main content
        if main_content:
            # Extract paragraphs
            paragraphs = []
            for p in main_content.find_all(["p", "h2", "h3", "h4", "li"]):
                text = p.get_text(strip=True)
                if len(text) > 15:  # Skip very short lines
                    paragraphs.append(text)
            
            content = "\n\n".join(paragraphs)
            
            # If content is suspiciously short, try broader extraction from body
            if len(content) < 200:
                body = soup.find("body")
                if body:
                    broader_paragraphs = []
                    for p in body.find_all(["p", "h1", "h2", "h3", "h4", "li"]):
                        text = p.get_text(strip=True)
                        if len(text) > 20:
                            broader_paragraphs.append(text)
                    
                    broader_content = "\n\n".join(broader_paragraphs)
                    if len(broader_content) > len(content):
                        content = broader_content
            
            result["content"] = content
            result["word_count"] = len(result["content"].split())
            result["reading_time"] = max(1, result["word_count"] // 200)  # ~200 wpm
        else:
            result["content"] = ""
            result["word_count"] = 0
            result["reading_time"] = 0
        
        # Images
        result["images"] = self._extract_images(main_content or soup)
        
        # Language
        result["language"] = self._detect_language(soup, result.get("content", ""))
        
        return result
    
    def _extract_product(self, soup: BeautifulSoup, main_content: Tag, schema_data: dict) -> dict:
        """Extract product-specific fields."""
        result = {}
        
        # Name
        result["name"] = (
            schema_data.get("name") or
            schema_data.get("title") or
            self._find_text(soup, "h1") or
            ""
        )
        
        # Price (Vietnamese format: 1.500.000đ, 1,5 triệu, 15tr, 500k)
        result["price"], result["currency"] = self._extract_price(soup, schema_data)
        
        # Original price (before discount)
        result["original_price"] = self._extract_original_price(soup)
        
        # Discount
        if result["original_price"] and result["price"]:
            try:
                discount_pct = (1 - result["price"] / result["original_price"]) * 100
                result["discount"] = f"{discount_pct:.0f}%"
            except:
                result["discount"] = ""
        else:
            result["discount"] = ""
        
        # Availability
        result["availability"] = self._extract_availability(soup, schema_data)
        
        # Description
        result["description"] = (
            schema_data.get("description") or
            self._find_text(soup, ".description, .product-description, .desc") or
            ""
        )
        
        # Specifications (key-value pairs)
        result["specifications"] = self._extract_specifications(soup)
        
        # Images
        result["images"] = self._extract_images(main_content or soup)
        
        # Rating and reviews
        result["rating"] = self._extract_rating(soup, schema_data)
        result["review_count"] = self._extract_review_count(soup, schema_data)
        
        # Brand
        result["brand"] = (
            schema_data.get("brand") or
            self._find_text(soup, ".brand, [itemprop='brand']") or
            ""
        )
        
        # SKU
        result["sku"] = (
            schema_data.get("sku") or
            self._find_text(soup, ".sku, [itemprop='sku']") or
            ""
        )
        
        # Category
        result["category"] = self._extract_category(soup)
        
        return result
    
    def _extract_listing(self, soup: BeautifulSoup, main_content: Tag, schema_data: dict) -> dict:
        """Extract listing items."""
        result = {}
        
        # Page title
        result["title"] = (
            schema_data.get("title") or
            self._find_text(soup, "h1") or
            ""
        )
        
        # Find repeated items
        items = []
        
        # Common listing selectors
        item_selectors = [
            ".item, .card, .listing-item, .grid-item, .product-item",
            "article",
            "li.item, li.card",
            ".result-item",
        ]
        
        for selector in item_selectors:
            try:
                elements = soup.select(selector)
                
                if len(elements) >= 3:  # Must have at least 3 items
                    for elem in elements[:50]:  # Limit to 50 items
                        item = self._extract_listing_item(elem)
                        if item and item.get("title"):
                            items.append(item)
                    
                    if items:
                        break  # Found items, stop looking
            except:
                pass
        
        result["items"] = items
        result["total_items"] = len(items)
        
        # Detect listing type
        if "product" in str(soup)[:2000].lower() or "price" in str(soup)[:2000].lower():
            result["page_type"] = "product_listing"
        elif "search" in str(soup)[:1000].lower() or "results" in str(soup)[:1000].lower():
            result["page_type"] = "search_results"
        else:
            result["page_type"] = "news_listing"
        
        # Pagination
        result["pagination"] = self._extract_pagination(soup)
        
        return result
    
    def _extract_listing_item(self, element: Tag) -> Optional[dict]:
        """Extract a single item from a listing."""
        item = {}
        
        # Find title/link
        link = element.select_one("a[href], h1 a, h2 a, h3 a, .title a")
        if link:
            item["title"] = link.get_text(strip=True)
            item["url"] = link.get("href", "")
        else:
            # Try to find title without link
            title_elem = element.select_one("h1, h2, h3, .title, .name")
            if title_elem:
                item["title"] = title_elem.get_text(strip=True)
            else:
                return None  # No title found
        
        # Summary/description
        desc = element.select_one("p, .description, .summary, .excerpt")
        if desc:
            item["summary"] = desc.get_text(strip=True)[:200]
        
        # Image
        img = element.select_one("img")
        if img:
            item["image"] = img.get("src") or img.get("data-src", "")
        
        # Price (if product listing)
        price_elem = element.select_one(".price, [itemprop='price']")
        if price_elem:
            item["price"] = price_elem.get_text(strip=True)
        
        # Metadata (date, author, etc.)
        metadata = {}
        
        date = element.select_one("time, .date, .datetime")
        if date:
            metadata["date"] = date.get_text(strip=True)
        
        author = element.select_one(".author, .byline")
        if author:
            metadata["author"] = author.get_text(strip=True)
        
        if metadata:
            item["metadata"] = metadata
        
        return item
    
    def _extract_forum(self, soup: BeautifulSoup, main_content: Tag, schema_data: dict) -> dict:
        """Extract forum/discussion content."""
        result = {}
        
        # Thread title
        result["title"] = (
            schema_data.get("title") or
            self._find_text(soup, "h1") or
            ""
        )
        
        # Posts
        posts = []
        
        post_selectors = [".post, .message, .comment, .reply, article"]
        
        for selector in post_selectors:
            try:
                elements = soup.select(selector)
                
                if len(elements) >= 2:  # At least original post + 1 reply
                    for elem in elements[:100]:  # Limit to 100 posts
                        post = self._extract_forum_post(elem)
                        if post:
                            posts.append(post)
                    
                    if posts:
                        break
            except:
                pass
        
        result["posts"] = posts
        result["post_count"] = len(posts)
        
        # Build content from all posts
        content_parts = []
        for post in posts:
            if post.get("author"):
                content_parts.append(f"**{post['author']}:**")
            content_parts.append(post.get("content", ""))
            content_parts.append("")  # blank line
        
        result["content"] = "\n".join(content_parts)
        
        return result
    
    def _extract_forum_post(self, element: Tag) -> Optional[dict]:
        """Extract a single forum post."""
        post = {}
        
        # Author
        author = element.select_one(".author, .username, .user")
        if author:
            post["author"] = author.get_text(strip=True)
        
        # Date
        date = element.select_one("time, .date, .datetime, .postdate")
        if date:
            post["date"] = date.get_text(strip=True)
        
        # Content
        content = element.select_one(".content, .message, .post-content, .text")
        if content:
            post["content"] = content.get_text(separator="\n", strip=True)
        else:
            # Fallback to element text
            post["content"] = element.get_text(separator="\n", strip=True)
        
        # Must have content
        if not post.get("content") or len(post["content"]) < 10:
            return None
        
        return post
    
    def _extract_generic(self, soup: BeautifulSoup, main_content: Tag, schema_data: dict) -> dict:
        """Generic extraction for unknown page types."""
        result = {}
        
        # Title
        result["title"] = (
            schema_data.get("title") or
            self._find_text(soup, "h1") or
            self._find_text(soup, "title") or
            ""
        )
        
        # Description
        result["description"] = schema_data.get("description", "")
        
        # Main content
        if main_content:
            content = main_content.get_text(separator="\n", strip=True)
            
            # If content is suspiciously short, try broader extraction
            if len(content) < 200:
                # Try getting all paragraphs from body
                body = soup.find("body")
                if body:
                    paragraphs = []
                    for p in body.find_all(["p", "h1", "h2", "h3", "h4", "li"]):
                        text = p.get_text(strip=True)
                        if len(text) > 20:  # Skip very short paragraphs
                            paragraphs.append(text)
                    
                    broader_content = "\n\n".join(paragraphs)
                    if len(broader_content) > len(content):
                        content = broader_content
            
            result["content"] = content
        else:
            result["content"] = ""
        
        # Images
        result["images"] = self._extract_images(main_content or soup)
        
        return result
    
    # Helper methods
    
    def _find_text(self, soup: BeautifulSoup, selector: str) -> str:
        """Find text content by selector."""
        try:
            elem = soup.select_one(selector)
            return elem.get_text(strip=True) if elem else ""
        except:
            return ""
    
    def _extract_date(self, soup: BeautifulSoup, schema_data: dict, date_type: str = "published") -> str:
        """Extract date (published or modified)."""
        # Try schema data first
        if date_type == "published":
            date = schema_data.get("published_time") or schema_data.get("datePublished", "")
        else:
            date = schema_data.get("modified_time") or schema_data.get("dateModified", "")
        
        if date:
            return date
        
        # Try HTML elements
        time_elem = soup.select_one("time[datetime], .date, .datetime, .published, .updated")
        if time_elem:
            return time_elem.get("datetime") or time_elem.get_text(strip=True)
        
        return ""
    
    def _extract_category(self, soup: BeautifulSoup) -> str:
        """Extract category from breadcrumb or nav."""
        breadcrumb = soup.select(".breadcrumb a, .breadcrumbs a")
        if breadcrumb and len(breadcrumb) > 1:
            # Return last breadcrumb (most specific)
            return breadcrumb[-1].get_text(strip=True)
        
        return ""
    
    def _extract_tags(self, soup: BeautifulSoup, schema_data: dict) -> list[str]:
        """Extract tags/keywords."""
        tags = schema_data.get("keywords", [])
        
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",")]
        
        # Also check tag elements
        tag_elems = soup.select(".tag, .label, .topic, .keyword")
        for elem in tag_elems:
            tag = elem.get_text(strip=True)
            if tag and tag not in tags:
                tags.append(tag)
        
        return tags[:20]  # Limit to 20 tags
    
    def _extract_images(self, element: Tag) -> list[dict]:
        """Extract images with alt text."""
        images = []
        
        for img in element.find_all("img")[:20]:  # Limit to 20 images
            src = img.get("src") or img.get("data-src") or img.get("data-lazy", "")
            alt = img.get("alt", "")
            
            if src and src.startswith("http"):
                images.append({"url": src, "alt": alt})
        
        return images
    
    def _get_first_paragraph(self, element: Optional[Tag]) -> str:
        """Get first meaningful paragraph."""
        if not element:
            return ""
        
        for p in element.find_all("p"):
            text = p.get_text(strip=True)
            if len(text) > 50:
                return text[:300]
        
        return ""
    
    def _extract_price(self, soup: BeautifulSoup, schema_data: dict) -> tuple[Optional[float], str]:
        """Extract price in multiple formats."""
        # Try schema data first
        if schema_data.get("price"):
            try:
                price = float(str(schema_data["price"]).replace(",", ""))
                currency = schema_data.get("priceCurrency", "VND")
                return price, currency
            except:
                pass
        
        # Try to find price in HTML
        price_elem = soup.select_one(".price, [itemprop='price'], .product-price")
        if not price_elem:
            return None, "VND"
        
        price_text = price_elem.get_text(strip=True)
        
        # Parse Vietnamese price formats
        # 1.500.000đ, 1,5 triệu, 15tr, 500k
        price_text = price_text.replace("₫", "").replace("đ", "").replace("VND", "").replace("vnđ", "").strip()
        
        # Handle "triệu" (million) and "k" (thousand)
        multiplier = 1
        if "triệu" in price_text.lower():
            multiplier = 1_000_000
            price_text = price_text.lower().replace("triệu", "").strip()
        elif "tr" in price_text.lower() and len(price_text) < 10:
            multiplier = 1_000_000
            price_text = price_text.lower().replace("tr", "").strip()
        elif price_text.endswith("k") or price_text.endswith("K"):
            multiplier = 1_000
            price_text = price_text[:-1].strip()
        
        # Remove dots and commas
        price_text = price_text.replace(".", "").replace(",", ".")
        
        # Extract number
        match = re.search(r'[\d.,]+', price_text)
        if match:
            try:
                price = float(match.group()) * multiplier
                return price, "VND"
            except:
                pass
        
        return None, "VND"
    
    def _extract_original_price(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract original price (before discount)."""
        elem = soup.select_one(".original-price, .old-price, .price-old, del .price, s .price")
        if elem:
            price_text = elem.get_text(strip=True)
            price, _ = self._extract_price(BeautifulSoup(f'<span class="price">{price_text}</span>', "lxml"), {})
            return price
        
        return None
    
    def _extract_availability(self, soup: BeautifulSoup, schema_data: dict) -> str:
        """Extract product availability."""
        avail = schema_data.get("availability", "")
        if avail:
            return avail
        
        # Check text patterns
        text = soup.get_text()[:2000].lower()
        
        if any(s in text for s in ["còn hàng", "in stock", "available"]):
            return "in_stock"
        elif any(s in text for s in ["hết hàng", "out of stock", "sold out"]):
            return "out_of_stock"
        elif any(s in text for s in ["đặt trước", "pre-order", "coming soon"]):
            return "pre_order"
        
        return "unknown"
    
    def _extract_specifications(self, soup: BeautifulSoup) -> dict:
        """Extract product specifications (key-value pairs)."""
        specs = {}
        
        # Look for spec tables
        table = soup.select_one(".specifications, .specs, .attributes, table.product-attributes")
        if table:
            for row in table.find_all("tr")[:30]:  # Limit to 30 specs
                cells = row.find_all(["th", "td"])
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    if key and value:
                        specs[key] = value
        
        # Also look for dl (definition list)
        dl = soup.select_one("dl.specs, dl.specifications")
        if dl:
            dts = dl.find_all("dt")
            dds = dl.find_all("dd")
            for dt, dd in zip(dts, dds):
                key = dt.get_text(strip=True)
                value = dd.get_text(strip=True)
                if key and value:
                    specs[key] = value
        
        return specs
    
    def _extract_rating(self, soup: BeautifulSoup, schema_data: dict) -> float:
        """Extract product rating."""
        # Try schema data
        if "aggregateRating" in schema_data:
            rating = schema_data["aggregateRating"]
            if isinstance(rating, dict):
                return float(rating.get("ratingValue", 0))
        
        # Try HTML
        rating_elem = soup.select_one("[itemprop='ratingValue'], .rating-value, .star-rating")
        if rating_elem:
            text = rating_elem.get_text(strip=True)
            match = re.search(r'[\d.]+', text)
            if match:
                try:
                    return float(match.group())
                except:
                    pass
        
        return 0.0
    
    def _extract_review_count(self, soup: BeautifulSoup, schema_data: dict) -> int:
        """Extract review count."""
        # Try schema data
        if "aggregateRating" in schema_data:
            rating = schema_data["aggregateRating"]
            if isinstance(rating, dict):
                count = rating.get("reviewCount", 0)
                try:
                    return int(count)
                except:
                    pass
        
        # Try HTML
        review_elem = soup.select_one(".review-count, [itemprop='reviewCount']")
        if review_elem:
            text = review_elem.get_text(strip=True)
            match = re.search(r'\d+', text)
            if match:
                try:
                    return int(match.group())
                except:
                    pass
        
        return 0
    
    def _extract_pagination(self, soup: BeautifulSoup) -> dict:
        """Extract pagination info."""
        pagination = {}
        
        # Current page
        current = soup.select_one(".current, .active, .pagination .active")
        if current:
            try:
                pagination["current"] = int(current.get_text(strip=True))
            except:
                pagination["current"] = 1
        
        # Total pages
        page_links = soup.select(".pagination a, .pager a")
        if page_links:
            page_numbers = []
            for link in page_links:
                try:
                    num = int(link.get_text(strip=True))
                    page_numbers.append(num)
                except:
                    pass
            
            if page_numbers:
                pagination["total"] = max(page_numbers)
        
        # Next page URL
        next_link = soup.select_one("a.next, a[rel='next'], .pagination .next")
        if next_link:
            pagination["next_url"] = next_link.get("href", "")
        
        return pagination
    
    def _detect_language(self, soup: BeautifulSoup, text: str) -> str:
        """Detect language from HTML or content."""
        # Check HTML lang attribute
        html_tag = soup.find("html")
        if html_tag and html_tag.get("lang"):
            return html_tag["lang"][:2]  # Return language code (e.g., "en", "vi")
        
        # Simple heuristic: check for Vietnamese characters
        if text and re.search(r'[àáảãạăắằẳẵặâấầẩẫậđèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵ]', text.lower()):
            return "vi"
        
        return "en"  # Default to English
    
    def _calculate_confidence(self, content_type: str, result: dict, schema_data: dict) -> float:
        """
        Calculate confidence score for extraction.
        
        Args:
            content_type: Detected content type
            result: Extraction result
            schema_data: Schema metadata
            
        Returns:
            Confidence score 0.0-1.0
        """
        confidence = 0.5  # Base confidence
        
        # Boost for schema data presence
        if schema_data.get("jsonld"):
            confidence += 0.2
        elif schema_data.get("type"):
            confidence += 0.1
        
        # Boost for content-type specific signals
        if content_type == "article":
            if result.get("author"):
                confidence += 0.1
            if result.get("published_date"):
                confidence += 0.1
            if result.get("word_count", 0) > 300:
                confidence += 0.1
        
        elif content_type == "product":
            if result.get("price"):
                confidence += 0.15
            if result.get("availability"):
                confidence += 0.1
            if result.get("images"):
                confidence += 0.05
        
        elif content_type == "listing":
            if result.get("total_items", 0) >= 5:
                confidence += 0.2
            elif result.get("total_items", 0) >= 3:
                confidence += 0.1
        
        # Cap at 1.0
        return min(confidence, 1.0)
    
    def _build_content_text(self, result: dict, content_type: str) -> str:
        """Build content text from extraction result."""
        if "content" in result and result["content"]:
            return result["content"]
        
        # Build from available fields
        parts = []
        
        if result.get("title"):
            parts.append(f"# {result['title']}")
        
        if result.get("description"):
            parts.append(result["description"])
        
        if result.get("summary"):
            parts.append(result["summary"])
        
        # For listings, build from items
        if content_type == "listing" and result.get("items"):
            parts.append("\n## Items\n")
            for item in result["items"][:30]:
                parts.append(f"**{item.get('title', '')}**")
                if item.get("summary"):
                    parts.append(item["summary"])
                parts.append("")
        
        return "\n\n".join(parts)
