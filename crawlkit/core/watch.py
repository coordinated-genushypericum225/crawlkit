"""
Real-time URL monitoring module.

Features:
- Register URLs to monitor
- Detect content changes via hash comparison
- Webhook callbacks on change detection
- Supabase storage
"""

from __future__ import annotations
import hashlib
import httpx
from typing import Optional
from datetime import datetime


def compute_content_hash(content: str) -> str:
    """
    Compute hash of content for change detection.
    
    Args:
        content: Text content to hash
    
    Returns:
        SHA256 hash as hex string
    """
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


class WatchManager:
    """Manage URL watches."""
    
    def __init__(self, db_client):
        """
        Initialize watch manager.
        
        Args:
            db_client: Supabase client from crawlkit.db
        """
        self.db = db_client
    
    def create_watch(
        self,
        url: str,
        api_key_id: str,
        webhook_url: Optional[str] = None,
        check_interval_minutes: int = 60,
        selector: Optional[str] = None,
    ) -> dict:
        """
        Register a URL to monitor.
        
        Args:
            url: URL to watch
            api_key_id: API key ID that owns this watch
            webhook_url: Callback URL on change detection
            check_interval_minutes: How often to check (default 60 min)
            selector: CSS selector to monitor specific element (optional)
        
        Returns:
            Created watch record
        """
        watch_data = {
            "url": url,
            "api_key_id": api_key_id,
            "webhook_url": webhook_url,
            "check_interval_minutes": check_interval_minutes,
            "selector": selector,
            "content_hash": None,  # Will be set on first check
            "last_checked_at": None,
            "last_changed_at": None,
            "is_active": True,
            "created_at": datetime.utcnow().isoformat(),
        }
        
        return self.db.insert("ck_watches", watch_data)
    
    def get_watches(self, api_key_id: str, is_active: bool = True) -> list[dict]:
        """
        Get watches for an API key.
        
        Args:
            api_key_id: API key ID
            is_active: Filter by active status
        
        Returns:
            List of watch records
        """
        return self.db.query(
            "ck_watches",
            api_key_id=api_key_id,
            is_active=is_active
        )
    
    def get_watch(self, watch_id: str) -> Optional[dict]:
        """
        Get a specific watch.
        
        Args:
            watch_id: Watch ID
        
        Returns:
            Watch record or None
        """
        results = self.db.query("ck_watches", id=watch_id)
        return results[0] if results else None
    
    def remove_watch(self, watch_id: str, api_key_id: str) -> bool:
        """
        Remove (deactivate) a watch.
        
        Args:
            watch_id: Watch ID
            api_key_id: API key ID (for ownership check)
        
        Returns:
            True if successful
        """
        try:
            self.db.update(
                "ck_watches",
                {"is_active": False},
                id=watch_id,
                api_key_id=api_key_id
            )
            return True
        except Exception as e:
            print(f"Failed to remove watch: {e}")
            return False
    
    def check_watch(self, watch_id: str, current_content: str) -> dict:
        """
        Check if a watch has detected changes.
        
        Args:
            watch_id: Watch ID
            current_content: Current page content
        
        Returns:
            Dict with change detection results
        """
        watch = self.get_watch(watch_id)
        if not watch:
            return {"error": "Watch not found"}
        
        # Compute current hash
        current_hash = compute_content_hash(current_content)
        previous_hash = watch.get("content_hash")
        
        # Update last checked time
        self.db.update(
            "ck_watches",
            {"last_checked_at": datetime.utcnow().isoformat()},
            id=watch_id
        )
        
        # If first check, store hash
        if previous_hash is None:
            self.db.update(
                "ck_watches",
                {
                    "content_hash": current_hash,
                    "last_changed_at": datetime.utcnow().isoformat()
                },
                id=watch_id
            )
            return {
                "changed": False,
                "first_check": True,
                "hash": current_hash
            }
        
        # Check for changes
        changed = current_hash != previous_hash
        
        if changed:
            # Update hash and last changed time
            self.db.update(
                "ck_watches",
                {
                    "content_hash": current_hash,
                    "last_changed_at": datetime.utcnow().isoformat()
                },
                id=watch_id
            )
            
            # Trigger webhook if configured
            if watch.get("webhook_url"):
                self._trigger_webhook(watch, current_content)
        
        return {
            "changed": changed,
            "first_check": False,
            "previous_hash": previous_hash,
            "current_hash": current_hash,
        }
    
    def _trigger_webhook(self, watch: dict, content: str):
        """
        Trigger webhook callback on change detection.
        
        Args:
            watch: Watch record
            content: New content
        """
        webhook_url = watch.get("webhook_url")
        if not webhook_url:
            return
        
        try:
            payload = {
                "watch_id": watch["id"],
                "url": watch["url"],
                "changed_at": datetime.utcnow().isoformat(),
                "content_preview": content[:500],  # First 500 chars
            }
            
            with httpx.Client(timeout=10) as client:
                response = client.post(webhook_url, json=payload)
                response.raise_for_status()
                print(f"✅ Webhook triggered for watch {watch['id']}")
        
        except Exception as e:
            print(f"⚠️ Webhook failed for watch {watch['id']}: {e}")
    
    def get_watches_to_check(self, limit: int = 100) -> list[dict]:
        """
        Get watches that need checking (based on check_interval).
        
        Args:
            limit: Maximum number of watches to return
        
        Returns:
            List of watch records
        """
        # This would require a more complex query with timestamp comparison
        # For now, return all active watches
        try:
            all_watches = self.db.query("ck_watches", is_active=True)
            
            # Filter by check interval
            now = datetime.utcnow()
            watches_to_check = []
            
            for watch in all_watches[:limit]:
                last_checked = watch.get("last_checked_at")
                interval = watch.get("check_interval_minutes", 60)
                
                if not last_checked:
                    # Never checked, add it
                    watches_to_check.append(watch)
                else:
                    # Check if interval has passed
                    last_checked_dt = datetime.fromisoformat(last_checked.replace('Z', '+00:00'))
                    minutes_since = (now - last_checked_dt).total_seconds() / 60
                    
                    if minutes_since >= interval:
                        watches_to_check.append(watch)
            
            return watches_to_check
        
        except Exception as e:
            print(f"Failed to get watches to check: {e}")
            return []


def get_watch_manager():
    """Get or create global watch manager."""
    from .. import db
    return WatchManager(db.get_db())
