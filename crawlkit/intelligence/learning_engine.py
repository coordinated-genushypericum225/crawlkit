"""
Learning Engine - Self-improving extraction that learns from every crawl.

The data moat: learns extraction patterns from successful crawls,
then reuses them for faster, more accurate extraction on future crawls.

Flow:
1. Crawl succeeds → extract quality score → identify selectors → store pattern
2. New crawl → check for learned pattern → if good match, use it (10x faster)
3. Pattern confidence improves with more samples
"""

from __future__ import annotations
import re
import hashlib
import logging
from typing import Optional
from urllib.parse import urlparse
from datetime import datetime
from bs4 import BeautifulSoup, Tag

from .pattern_storage import PatternStorage, SitePattern

logger = logging.getLogger(__name__)


class LearningEngine:
    """
    Self-improving extraction engine — learns from every crawl.
    
    This is CrawlKit's competitive moat: the more you crawl a domain,
    the better the extraction becomes.
    """
    
    def __init__(self, storage: PatternStorage):
        """Initialize learning engine with pattern storage."""
        self.storage = storage
        self._cache = {}  # In-memory cache for current session
    
    def learn_from_crawl(
        self,
        url: str,
        html: str,
        extraction_result: dict,
        quality_score: float,
    ):
        """
        After a successful crawl, learn patterns from it.
        
        Args:
            url: The URL that was crawled
            html: The HTML content
            extraction_result: The extraction result (with content, title, metadata)
            quality_score: Quality assessment 0.0-1.0
        """
        # Don't learn from low-quality extractions
        if quality_score < 0.5:
            logger.debug(f"Skipping learning from low-quality extraction: {url}")
            return
        
        domain = self._get_domain(url)
        fingerprint = self._fingerprint_page(html)
        
        # Identify selectors that match the extracted content
        content_selectors = self._identify_selectors(html, extraction_result)
        noise_selectors = self._identify_noise(html)
        
        # Build pattern
        pattern = SitePattern(
            domain=domain,
            url_pattern=self._generalize_url(url),
            content_selectors=content_selectors,
            title_selector=self._identify_title_selector(html, extraction_result),
            author_selector=self._identify_author_selector(html, extraction_result),
            date_selector=self._identify_date_selector(html, extraction_result),
            noise_selectors=noise_selectors,
            content_type=extraction_result.get('content_type', 'generic'),
            quality_score=quality_score,
            fingerprint=fingerprint,
            sample_count=1,
            last_seen=datetime.utcnow(),
        )
        
        # Store pattern
        self.storage.upsert_pattern(pattern)
        logger.info(f"📚 Learned pattern for {domain} (quality: {quality_score:.2f})")
    
    def get_pattern(self, url: str, html: str) -> Optional[SitePattern]:
        """
        Look up learned pattern for this URL/domain.
        
        Returns best matching pattern if confidence > 0.7, else None.
        """
        domain = self._get_domain(url)
        
        # 1. Exact domain match
        patterns = self.storage.get_patterns(domain)
        if patterns:
            # Find best matching pattern by URL pattern
            best = self._find_best_match(url, html, patterns)
            if best and best.quality_score > 0.7:
                logger.info(f"✅ Using learned pattern for {domain} (uses: {best.sample_count})")
                return best
        
        # 2. Similar domain pattern (e.g., news sites share patterns)
        similar = self.storage.find_similar_patterns(html)
        if similar:
            pattern = similar[0]
            logger.info(f"✅ Using similar pattern from {pattern.domain} (fingerprint match)")
            return pattern
        
        return None
    
    def apply_pattern(self, html: str, pattern: SitePattern) -> dict:
        """
        Apply a learned pattern to extract content.
        
        Returns extraction result dict.
        """
        soup = BeautifulSoup(html, 'lxml')
        
        # Remove noise using learned noise selectors
        for selector in pattern.noise_selectors:
            try:
                for el in soup.select(selector):
                    el.decompose()
            except Exception as e:
                logger.warning(f"Failed to apply noise selector {selector}: {e}")
        
        # Extract content using learned content selectors
        content = ""
        for selector in pattern.content_selectors:
            try:
                el = soup.select_one(selector)
                if el:
                    content = el.get_text(separator="\n", strip=True)
                    break
            except Exception as e:
                logger.warning(f"Failed to apply content selector {selector}: {e}")
        
        # Extract title
        title = ""
        if pattern.title_selector:
            try:
                el = soup.select_one(pattern.title_selector)
                if el:
                    title = el.get_text(strip=True)
            except Exception:
                pass
        
        # Extract metadata using learned selectors
        metadata = {}
        
        if pattern.author_selector:
            try:
                el = soup.select_one(pattern.author_selector)
                if el:
                    metadata["author"] = el.get_text(strip=True)
            except Exception:
                pass
        
        if pattern.date_selector:
            try:
                el = soup.select_one(pattern.date_selector)
                if el:
                    metadata["published_date"] = el.get_text(strip=True)
            except Exception:
                pass
        
        return {
            "content": content,
            "title": title,
            "content_type": pattern.content_type,
            "extraction_confidence": pattern.quality_score,
            "parser_used": f"learned:{pattern.domain}",
            "pattern_uses": pattern.sample_count,
            "extracted": metadata,
        }
    
    def update_domain_stats(self, url: str, result: dict):
        """Update domain statistics (async, non-blocking)."""
        domain = self._get_domain(url)
        success = bool(result.get("content"))
        quality = result.get("extraction_confidence", 0.5)
        content_length = len(result.get("content", ""))
        content_type = result.get("content_type", "generic")
        
        self.storage.update_domain_stats(domain, success, quality, content_length, content_type)
    
    # ===== Helper Methods =====
    
    def _get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        return urlparse(url).netloc.lower().replace("www.", "")
    
    def _fingerprint_page(self, html: str) -> str:
        """
        Create structural fingerprint of the page.
        
        Pages with same DOM structure = same extraction pattern.
        Ignores text content, only looks at tag hierarchy.
        """
        return self._fingerprint_page_static(html)
    
    @staticmethod
    def _fingerprint_page_static(html: str) -> str:
        """Static version for use in pattern_storage.py."""
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            def get_structure(el, depth=0, max_depth=4):
                """Build tag hierarchy string."""
                if depth > max_depth or not hasattr(el, 'name'):
                    return ''
                
                # Get children tags (ignore text nodes)
                children = [
                    get_structure(c, depth+1, max_depth)
                    for c in el.children
                    if hasattr(c, 'name')
                ]
                
                # Limit children to avoid huge strings
                children = children[:5]
                children_str = ','.join(children) if children else ''
                
                return f"{el.name}({children_str})"
            
            body = soup.find('body')
            if not body:
                # Fallback: hash first 1000 chars
                return hashlib.md5(html[:1000].encode()).hexdigest()[:16]
            
            structure = get_structure(body)
            return hashlib.md5(structure.encode()).hexdigest()[:16]
        except Exception as e:
            logger.warning(f"Fingerprinting failed: {e}")
            return hashlib.md5(html[:1000].encode()).hexdigest()[:16]
    
    def _generalize_url(self, url: str) -> str:
        """
        Convert specific URL to pattern.
        
        Examples:
        - https://vnexpress.net/bai-viet-123.html → vnexpress.net/{slug}.html
        - https://cafef.vn/stock/VNM-123.chn → cafef.vn/stock/{id}.chn
        - https://example.com/news/2024/03/article → example.com/news/{year}/{month}/{slug}
        """
        parsed = urlparse(url)
        path = parsed.path
        
        # Replace numbers with placeholders
        path = re.sub(r'\d{4}', '{year}', path, count=1)  # Year
        path = re.sub(r'\d{2}', '{month}', path, count=1)  # Month
        path = re.sub(r'\d+', '{id}', path)  # Other numbers
        
        # Replace slugs (words separated by dashes/underscores)
        path = re.sub(r'[a-z0-9]+-[a-z0-9-]+', '{slug}', path)
        
        return f"{parsed.netloc}{path}"
    
    def _identify_selectors(self, html: str, result: dict) -> list[str]:
        """
        Identify CSS selectors that match extracted content.
        
        Given the extracted content, find which DOM elements contain it.
        Returns the most specific CSS selectors.
        """
        content_text = result.get('content', '')
        if not content_text or len(content_text) < 50:
            return []
        
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # Find elements containing the extracted content
            candidates = []
            for el in soup.find_all(True):
                el_text = el.get_text(separator=" ", strip=True)
                if not el_text or len(el_text) < 50:
                    continue
                
                # Calculate overlap with extracted content
                overlap = self._text_overlap(el_text, content_text)
                if overlap > 0.8:
                    selector = self._build_selector(el)
                    if selector:
                        candidates.append((selector, overlap, len(el_text)))
            
            # Pick most specific selector with highest overlap
            # Prefer shorter element text (more specific)
            candidates.sort(key=lambda x: (x[1], -x[2]), reverse=True)
            return [c[0] for c in candidates[:3]]
        except Exception as e:
            logger.warning(f"Selector identification failed: {e}")
            return []
    
    def _identify_title_selector(self, html: str, result: dict) -> Optional[str]:
        """Identify CSS selector for title."""
        title = result.get('title', '')
        if not title or len(title) < 5:
            return None
        
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # Find element containing exact title text
            for el in soup.find_all(['h1', 'h2', 'title']):
                if title in el.get_text(strip=True):
                    selector = self._build_selector(el)
                    if selector:
                        return selector
        except Exception:
            pass
        
        return None
    
    def _identify_author_selector(self, html: str, result: dict) -> Optional[str]:
        """Identify CSS selector for author."""
        author = result.get('extracted', {}).get('author', '')
        if not author:
            return None
        
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # Find element containing author text
            for el in soup.find_all(['span', 'a', 'div', 'p']):
                if author in el.get_text(strip=True):
                    selector = self._build_selector(el)
                    if selector:
                        return selector
        except Exception:
            pass
        
        return None
    
    def _identify_date_selector(self, html: str, result: dict) -> Optional[str]:
        """Identify CSS selector for date."""
        date = result.get('extracted', {}).get('published_date', '')
        if not date:
            return None
        
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # Find time element or element with date
            for el in soup.find_all(['time', 'span', 'div']):
                if date in el.get_text(strip=True):
                    selector = self._build_selector(el)
                    if selector:
                        return selector
        except Exception:
            pass
        
        return None
    
    def _identify_noise(self, html: str) -> list[str]:
        """
        Identify CSS selectors for noise elements.
        
        Common noise: nav, footer, sidebar, ads, social sharing, comments.
        """
        noise_selectors = []
        
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # Common noise elements
            noise_tags = [
                'nav', 'footer', 'aside', 'header',
                '.sidebar', '.menu', '.navigation',
                '.comments', '.comment-section',
                '.social-share', '.share-buttons',
                '.advertisement', '.ad', '.ads',
                '.related-articles', '.recommended',
                '#comments', '#sidebar',
            ]
            
            for selector in noise_tags:
                if soup.select(selector):
                    noise_selectors.append(selector)
        except Exception as e:
            logger.warning(f"Noise identification failed: {e}")
        
        return noise_selectors
    
    def _build_selector(self, element: Tag) -> Optional[str]:
        """
        Build a CSS selector for an element.
        
        Priority:
        1. Use stable ID (not dynamic)
        2. Use stable classes (not CSS-in-JS or random hashes)
        3. Use tag + parent context
        """
        tag = element.name
        
        # Try ID (if stable)
        el_id = element.get('id', '')
        if el_id and not re.match(r'^\d+$|^[a-f0-9]{8,}$|^[a-z]{1,2}\d+', el_id):
            return f"#{el_id}"
        
        # Try classes (if stable)
        classes = element.get('class', [])
        if classes:
            # Filter out dynamic/random classes
            stable_classes = [
                c for c in classes
                if not re.match(r'^[a-z]{1,2}\d+|^css-|^_[a-f0-9]{6}', c)
            ]
            if stable_classes:
                return f"{tag}.{'.'.join(stable_classes[:2])}"
        
        # Try semantic tags
        if tag in ['article', 'main', 'section']:
            return tag
        
        # Use tag + parent context (limited depth)
        parent = element.parent
        if parent and hasattr(parent, 'name'):
            parent_sel = self._build_simple_selector(parent)
            if parent_sel:
                return f"{parent_sel} > {tag}"
        
        return tag
    
    def _build_simple_selector(self, element: Tag) -> Optional[str]:
        """Build simple selector without recursion."""
        tag = element.name
        el_id = element.get('id', '')
        
        if el_id and not re.match(r'^\d+$|^[a-f0-9]{8,}$', el_id):
            return f"#{el_id}"
        
        classes = element.get('class', [])
        if classes:
            stable = [c for c in classes if not re.match(r'^[a-z]{1,2}\d+|^css-', c)]
            if stable:
                return f"{tag}.{stable[0]}"
        
        return tag
    
    def _text_overlap(self, text1: str, text2: str) -> float:
        """
        Calculate text overlap ratio (0.0-1.0).
        
        Uses simple word-based Jaccard similarity.
        """
        # Normalize
        words1 = set(re.findall(r'\w+', text1.lower()))
        words2 = set(re.findall(r'\w+', text2.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        # Jaccard similarity
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def _find_best_match(self, url: str, html: str, patterns: list[SitePattern]) -> Optional[SitePattern]:
        """
        Find best matching pattern for URL/HTML.
        
        Scoring:
        1. URL pattern match (exact > partial)
        2. Fingerprint match (exact > none)
        3. Quality score (higher better)
        4. Sample count (more samples = more reliable)
        """
        url_pattern = self._generalize_url(url)
        fingerprint = self._fingerprint_page(html)
        
        scored_patterns = []
        for pattern in patterns:
            score = 0.0
            
            # URL pattern match
            if pattern.url_pattern == url_pattern:
                score += 0.4
            elif pattern.url_pattern in url_pattern or url_pattern in pattern.url_pattern:
                score += 0.2
            
            # Fingerprint match
            if pattern.fingerprint == fingerprint:
                score += 0.3
            
            # Quality score
            score += pattern.quality_score * 0.2
            
            # Sample count bonus (logarithmic)
            import math
            score += min(0.1, math.log10(pattern.sample_count + 1) * 0.05)
            
            scored_patterns.append((pattern, score))
        
        # Return best match
        scored_patterns.sort(key=lambda x: x[1], reverse=True)
        if scored_patterns and scored_patterns[0][1] > 0.5:
            return scored_patterns[0][0]
        
        return None
