"""
Pattern Storage - In-memory LRU cache + Supabase persistence for learned patterns.

Stores extraction patterns learned from successful crawls.
Fast in-memory cache for hot domains, async persistence to Supabase.
"""

from __future__ import annotations
import logging
from collections import OrderedDict
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional
import hashlib
import json

logger = logging.getLogger(__name__)


@dataclass
class SitePattern:
    """A learned extraction pattern for a domain/URL pattern."""
    domain: str
    url_pattern: str            # Generalized URL pattern (e.g., "vnexpress.net/{slug}.html")
    content_selectors: list[str]  # CSS selectors for main content
    title_selector: Optional[str] = None  # CSS selector for title
    author_selector: Optional[str] = None  # CSS selector for author
    date_selector: Optional[str] = None    # CSS selector for date
    noise_selectors: list[str] = None     # CSS selectors to remove
    content_type: str = "generic"          # article, product, listing
    quality_score: float = 0.5             # 0.0-1.0
    fingerprint: Optional[str] = None      # DOM structure hash
    sample_count: int = 1                  # How many times this pattern was seen
    last_seen: Optional[datetime] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialize defaults."""
        if self.noise_selectors is None:
            self.noise_selectors = []
        if self.last_seen is None:
            self.last_seen = datetime.utcnow()
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class LRUCache:
    """Simple LRU cache for hot domain patterns."""
    
    def __init__(self, maxsize: int = 1000):
        self._cache = OrderedDict()
        self._maxsize = maxsize
    
    def get(self, key: str) -> Optional[SitePattern]:
        """Get pattern from cache, moving to end (most recent)."""
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return None
    
    def put(self, key: str, value: SitePattern):
        """Store pattern in cache."""
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = value
        if len(self._cache) > self._maxsize:
            self._cache.popitem(last=False)  # Remove oldest
    
    def get_all(self) -> dict[str, SitePattern]:
        """Get all cached patterns."""
        return dict(self._cache)
    
    def size(self) -> int:
        """Current cache size."""
        return len(self._cache)


class PatternStorage:
    """
    Store and retrieve learned extraction patterns.
    
    Two-tier storage:
    1. In-memory LRU cache for fast lookups (hot domains)
    2. Supabase for persistence (async writes, sync reads on cache miss)
    """
    
    def __init__(self, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None):
        """Initialize pattern storage."""
        self._memory = LRUCache(maxsize=1000)
        self._db = None
        self._supabase_url = supabase_url
        self._supabase_key = supabase_key
        
        if supabase_url and supabase_key:
            self._init_db(supabase_url, supabase_key)
    
    def _init_db(self, url: str, key: str):
        """Initialize Supabase connection."""
        try:
            from supabase import create_client
            self._db = create_client(url, key)
            logger.info("✅ Pattern storage connected to Supabase")
        except Exception as e:
            logger.warning(f"⚠️ Supabase init failed: {e}. Using in-memory storage only.")
            self._db = None
    
    def upsert_pattern(self, pattern: SitePattern):
        """
        Store or update a pattern.
        
        Updates in-memory cache immediately (fast).
        Persists to Supabase async (non-blocking).
        """
        key = f"{pattern.domain}:{pattern.url_pattern}"
        
        # Update in-memory cache
        existing = self._memory.get(key)
        if existing:
            # Merge: increase sample_count, update quality_score (weighted avg)
            existing.sample_count += 1
            existing.quality_score = (existing.quality_score * 0.8 + pattern.quality_score * 0.2)
            existing.last_seen = pattern.last_seen
            
            # Merge selectors (keep unique)
            existing.content_selectors = list(set(existing.content_selectors + pattern.content_selectors))
            existing.noise_selectors = list(set(existing.noise_selectors + pattern.noise_selectors))
            
            # Update other selectors if new pattern has them
            if pattern.title_selector:
                existing.title_selector = pattern.title_selector
            if pattern.author_selector:
                existing.author_selector = pattern.author_selector
            if pattern.date_selector:
                existing.date_selector = pattern.date_selector
            
            self._memory.put(key, existing)
            pattern = existing
        else:
            self._memory.put(key, pattern)
        
        # Async persist to Supabase (non-blocking)
        if self._db:
            try:
                self._persist_to_db(pattern)
            except Exception as e:
                logger.warning(f"⚠️ Failed to persist pattern to DB: {e}")
    
    def _persist_to_db(self, pattern: SitePattern):
        """Write pattern to Supabase (upsert)."""
        data = {
            "domain": pattern.domain,
            "url_pattern": pattern.url_pattern,
            "content_selectors": pattern.content_selectors,
            "title_selector": pattern.title_selector,
            "author_selector": pattern.author_selector,
            "date_selector": pattern.date_selector,
            "noise_selectors": pattern.noise_selectors,
            "content_type": pattern.content_type,
            "quality_score": pattern.quality_score,
            "fingerprint": pattern.fingerprint,
            "sample_count": pattern.sample_count,
            "last_seen": pattern.last_seen.isoformat() if pattern.last_seen else None,
            "updated_at": datetime.utcnow().isoformat(),
        }
        
        # Upsert (insert or update on conflict)
        self._db.table("ck_site_patterns").upsert(data).execute()
    
    def get_patterns(self, domain: str) -> list[SitePattern]:
        """Get all patterns for a domain."""
        # Check cache first
        patterns = []
        for key, pattern in self._memory.get_all().items():
            if pattern.domain == domain:
                patterns.append(pattern)
        
        if patterns:
            return patterns
        
        # Cache miss — load from DB
        if self._db:
            try:
                response = self._db.table("ck_site_patterns").select("*").eq("domain", domain).execute()
                for row in response.data:
                    pattern = self._row_to_pattern(row)
                    patterns.append(pattern)
                    # Cache it
                    key = f"{pattern.domain}:{pattern.url_pattern}"
                    self._memory.put(key, pattern)
            except Exception as e:
                logger.warning(f"⚠️ Failed to load patterns from DB: {e}")
        
        return patterns
    
    def find_similar_patterns(self, html: str) -> list[SitePattern]:
        """Find patterns with similar DOM structure (by fingerprint)."""
        # Generate fingerprint for this HTML
        from .learning_engine import LearningEngine
        fingerprint = LearningEngine._fingerprint_page_static(html)
        
        # Check cache
        for pattern in self._memory.get_all().values():
            if pattern.fingerprint == fingerprint and pattern.quality_score > 0.6:
                return [pattern]
        
        # Check DB
        if self._db:
            try:
                response = self._db.table("ck_site_patterns") \
                    .select("*") \
                    .eq("fingerprint", fingerprint) \
                    .gte("quality_score", 0.6) \
                    .order("quality_score", desc=True) \
                    .limit(1) \
                    .execute()
                
                if response.data:
                    pattern = self._row_to_pattern(response.data[0])
                    return [pattern]
            except Exception as e:
                logger.warning(f"⚠️ Failed to find similar patterns: {e}")
        
        return []
    
    def get_stats(self) -> dict:
        """Get learning stats: domains known, patterns stored, etc."""
        cache_stats = {
            "cache_size": self._memory.size(),
            "cache_maxsize": self._memory._maxsize,
        }
        
        if not self._db:
            return {
                **cache_stats,
                "storage": "memory_only",
                "total_patterns": self._memory.size(),
            }
        
        # Get stats from DB
        try:
            # Count patterns
            patterns_count = self._db.table("ck_site_patterns").select("id", count="exact").execute()
            total_patterns = patterns_count.count if hasattr(patterns_count, 'count') else 0
            
            # Count domains
            domains = self._db.table("ck_site_patterns").select("domain").execute()
            unique_domains = len(set(row["domain"] for row in domains.data))
            
            # Avg quality
            all_patterns = self._db.table("ck_site_patterns").select("quality_score").execute()
            if all_patterns.data:
                avg_quality = sum(p["quality_score"] for p in all_patterns.data) / len(all_patterns.data)
            else:
                avg_quality = 0.0
            
            # Top domains
            domain_stats = self._db.table("ck_domain_stats") \
                .select("*") \
                .order("total_crawls", desc=True) \
                .limit(10) \
                .execute()
            
            return {
                **cache_stats,
                "storage": "supabase",
                "total_patterns": total_patterns,
                "unique_domains": unique_domains,
                "avg_quality": round(avg_quality, 3),
                "top_domains": domain_stats.data if domain_stats.data else [],
            }
        except Exception as e:
            logger.warning(f"⚠️ Failed to get stats from DB: {e}")
            return {
                **cache_stats,
                "storage": "supabase_error",
                "error": str(e),
            }
    
    def _row_to_pattern(self, row: dict) -> SitePattern:
        """Convert DB row to SitePattern."""
        return SitePattern(
            domain=row["domain"],
            url_pattern=row["url_pattern"],
            content_selectors=row.get("content_selectors", []),
            title_selector=row.get("title_selector"),
            author_selector=row.get("author_selector"),
            date_selector=row.get("date_selector"),
            noise_selectors=row.get("noise_selectors", []),
            content_type=row.get("content_type", "generic"),
            quality_score=row.get("quality_score", 0.5),
            fingerprint=row.get("fingerprint"),
            sample_count=row.get("sample_count", 1),
            last_seen=datetime.fromisoformat(row["last_seen"]) if row.get("last_seen") else None,
            created_at=datetime.fromisoformat(row["created_at"]) if row.get("created_at") else None,
        )
    
    def update_domain_stats(self, domain: str, success: bool, quality_score: float, content_length: int, content_type: str):
        """Update domain statistics (async)."""
        if not self._db:
            return
        
        try:
            # Get existing stats
            response = self._db.table("ck_domain_stats").select("*").eq("domain", domain).execute()
            
            if response.data:
                # Update existing
                stats = response.data[0]
                total = stats["total_crawls"] + 1
                successful = stats["successful_crawls"] + (1 if success else 0)
                
                # Weighted average quality
                old_avg = stats["avg_quality_score"]
                new_avg = (old_avg * stats["successful_crawls"] + quality_score) / successful if successful > 0 else old_avg
                
                # Weighted average length
                old_len = stats["avg_content_length"]
                new_len = (old_len * stats["successful_crawls"] + content_length) / successful if successful > 0 else old_len
                
                # Content type distribution
                types = stats.get("content_types", {})
                if isinstance(types, str):
                    types = json.loads(types)
                types[content_type] = types.get(content_type, 0) + 1
                
                update_data = {
                    "total_crawls": total,
                    "successful_crawls": successful,
                    "avg_quality_score": new_avg,
                    "avg_content_length": int(new_len),
                    "content_types": types,
                    "last_crawled": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                }
                
                self._db.table("ck_domain_stats").update(update_data).eq("domain", domain).execute()
            else:
                # Insert new
                insert_data = {
                    "domain": domain,
                    "total_crawls": 1,
                    "successful_crawls": 1 if success else 0,
                    "avg_quality_score": quality_score if success else 0.0,
                    "avg_content_length": content_length if success else 0,
                    "content_types": {content_type: 1},
                    "last_crawled": datetime.utcnow().isoformat(),
                    "first_crawled": datetime.utcnow().isoformat(),
                }
                
                self._db.table("ck_domain_stats").insert(insert_data).execute()
        except Exception as e:
            logger.warning(f"⚠️ Failed to update domain stats: {e}")
