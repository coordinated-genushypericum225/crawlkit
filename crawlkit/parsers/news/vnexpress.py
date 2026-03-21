"""
Parser for vnexpress.net — Vietnam's largest news site.

Extracts:
- Article title, description, author, date
- Article body (paragraphs)
- Category, tags
- Related articles
"""

from __future__ import annotations
import re
from typing import Any, Optional
from bs4 import BeautifulSoup

from ..base import BaseParser


class VnExpressParser(BaseParser):
    name = "vnexpress"
    domain = "vnexpress.net"
    
    def parse(self, html: str, url: str = "", text: str = "") -> dict[str, Any]:
        """Parse a VnExpress page (article or listing)."""
        soup = BeautifulSoup(html, "lxml")
        
        result = {
            "source": "vnexpress",
            "url": url,
        }
        
        # Detect if this is a listing page or article page
        is_article = soup.select_one("article.fck_detail, .article-content, .content-detail") is not None
        result["page_type"] = "article" if is_article else "listing"
        
        # Title
        title_el = soup.select_one("h1.title-detail, h1.title_news_detail, h1, .page-detail .title")
        result["title"] = title_el.get_text(strip=True) if title_el else ""
        
        # Description/Lead
        desc_el = soup.select_one("p.description, .sapo, .lead")
        result["description"] = desc_el.get_text(strip=True) if desc_el else ""
        
        # Category
        breadcrumb = soup.select(".breadcrumb a, .folder a")
        if breadcrumb:
            result["category"] = breadcrumb[-1].get_text(strip=True)
        
        if is_article:
            # Parse as article page
            # Author
            author_el = soup.select_one(".author_mail .name, .author, .article-author")
            result["author"] = author_el.get_text(strip=True) if author_el else ""
            
            # Date
            date_el = soup.select_one(".date, time, .datetime, .time-detail")
            if date_el:
                date_text = date_el.get_text(strip=True)
                result["date"] = date_text
                # Try to parse Vietnamese date format
                m = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', date_text)
                if m:
                    result["date_iso"] = f"{m.group(3)}-{m.group(2).zfill(2)}-{m.group(1).zfill(2)}"
            
            # Article body
            body_el = soup.select_one("article.fck_detail, .article-content, .content-detail")
            if body_el:
                # Extract paragraphs
                paragraphs = []
                for p in body_el.find_all(["p", "h2", "h3"]):
                    text = p.get_text(strip=True)
                    if text and len(text) > 10:
                        tag_name = p.name
                        paragraphs.append({
                            "type": "heading" if tag_name in ("h2", "h3") else "paragraph",
                            "content": text,
                        })
                
                result["paragraphs"] = paragraphs
                result["content"] = "\n\n".join(p["content"] for p in paragraphs)
                result["content_length"] = len(result["content"])
            
            # Tags
            tags_el = soup.select(".tags a, .topic-item a, .label_tag a")
            result["tags"] = [t.get_text(strip=True) for t in tags_el if t.get_text(strip=True)]
            
            # Related articles
            related = []
            for a in soup.select(".box-related a, .list-news-subfolder a"):
                href = a.get("href", "")
                title = a.get_text(strip=True)
                if title and href and len(title) > 10:
                    related.append({"title": title[:120], "url": href})
            result["related"] = related[:10]
        
        else:
            # Parse as listing page - extract article summaries
            articles = []
            
            # Find all article items in listing
            article_selectors = [
                ".item-news",
                ".list-news-subfolder .item-news",
                "article.item-news",
            ]
            
            for selector in article_selectors:
                for item in soup.select(selector):
                    # Extract article link and title
                    link_el = item.select_one("h3 a, h2 a, .title-news a")
                    if not link_el:
                        continue
                    
                    article_url = link_el.get("href", "")
                    article_title = link_el.get_text(strip=True)
                    
                    if not article_url or not article_title or len(article_title) < 10:
                        continue
                    
                    # Extract description/summary
                    desc_el = item.select_one("p.description, .description, p")
                    article_desc = desc_el.get_text(strip=True) if desc_el else ""
                    
                    articles.append({
                        "title": article_title,
                        "url": article_url,
                        "description": article_desc,
                    })
                    
                    # Limit to avoid huge outputs
                    if len(articles) >= 50:
                        break
                
                if len(articles) >= 50:
                    break
            
            result["articles"] = articles
            result["articles_count"] = len(articles)
            
            # Build content from articles for RAG/search purposes
            content_parts = []
            for art in articles[:30]:  # Limit to first 30 for content field
                content_parts.append(f"**{art['title']}**")
                if art.get("description"):
                    content_parts.append(art["description"])
                content_parts.append("")  # blank line
            
            result["content"] = "\n".join(content_parts)
            result["content_length"] = len(result["content"])
        
        return result
    
    def discover(self, query: Optional[str] = None, limit: int = 100) -> list[dict]:
        """
        Discover article URLs from VnExpress.
        
        Args:
            query: Category/section URL or None for homepage
            limit: Max URLs to return
        
        Returns:
            List of dicts with 'url' and 'title' keys
        """
        import httpx
        from urllib.parse import urljoin, urlparse
        
        # Use query as URL if provided, otherwise use homepage
        base_url = query if query and query.startswith("http") else "https://vnexpress.net"
        
        try:
            resp = httpx.get(base_url, timeout=15, follow_redirects=True)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, "lxml")
            
            # Find article links
            urls = []
            seen = set()
            
            # VnExpress article selectors
            article_selectors = [
                "article h3 a",
                "article h2 a",
                ".item-news h3 a",
                ".item-news h2 a",
                ".title-news a",
                "h3.title-news a",
                ".list-news-subfolder h3 a",
            ]
            
            for selector in article_selectors:
                for a in soup.select(selector):
                    href = a.get("href", "")
                    title = a.get_text(strip=True)
                    
                    # Skip if no href or title
                    if not href or not title or len(title) < 10:
                        continue
                    
                    # Make absolute URL
                    full_url = urljoin(base_url, href)
                    
                    # Must be vnexpress.net article (not video, photo galleries, etc.)
                    parsed = urlparse(full_url)
                    if "vnexpress.net" not in parsed.netloc:
                        continue
                    
                    # Skip duplicates
                    if full_url in seen:
                        continue
                    seen.add(full_url)
                    
                    # Add to results
                    urls.append({
                        "url": full_url,
                        "title": title,
                    })
                    
                    # Stop if we have enough
                    if len(urls) >= limit:
                        break
                
                if len(urls) >= limit:
                    break
            
            return urls[:limit]
        
        except Exception as e:
            # Return empty list on error (don't fail)
            return []
