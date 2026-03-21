"""
CrawlKit Database Module — Supabase REST API client

Handles authentication, API key management, and usage tracking.
Uses httpx for direct REST API calls (no supabase-py dependency).
"""

from __future__ import annotations
import os
import secrets
import hashlib
from typing import Optional
from datetime import datetime, date, timedelta
from dataclasses import dataclass

import httpx
import bcrypt


# ── Config ───────────────────────────────────────────────────────────

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://your-project.supabase.co")
SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

if not SERVICE_KEY:
    raise ValueError("SUPABASE_SERVICE_KEY environment variable required")


# ── Client ───────────────────────────────────────────────────────────

class SupabaseClient:
    """Simple Supabase REST API client using httpx."""
    
    def __init__(self):
        self.base_url = f"{SUPABASE_URL}/rest/v1"
        self.headers = {
            "apikey": SERVICE_KEY,
            "Authorization": f"Bearer {SERVICE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }
        self.client = httpx.Client(base_url=self.base_url, headers=self.headers, timeout=10.0)
    
    def query(self, table: str, select: str = "*", **filters) -> list[dict]:
        """Query table with filters."""
        params = {"select": select}
        params.update({f"{k}": f"eq.{v}" for k, v in filters.items()})
        
        resp = self.client.get(f"/{table}", params=params)
        resp.raise_for_status()
        return resp.json()
    
    def insert(self, table: str, data: dict | list[dict]) -> dict | list[dict]:
        """Insert row(s) into table."""
        resp = self.client.post(f"/{table}", json=data)
        resp.raise_for_status()
        result = resp.json()
        return result[0] if isinstance(data, dict) else result
    
    def update(self, table: str, data: dict, **filters) -> dict:
        """Update rows matching filters."""
        params = {f"{k}": f"eq.{v}" for k, v in filters.items()}
        resp = self.client.patch(f"/{table}", params=params, json=data)
        resp.raise_for_status()
        result = resp.json()
        return result[0] if result else {}
    
    def upsert(self, table: str, data: dict | list[dict], on_conflict: str = "") -> dict | list[dict]:
        """Upsert (insert or update) row(s)."""
        headers = self.headers.copy()
        headers["Prefer"] = "resolution=merge-duplicates,return=representation"
        
        resp = self.client.post(
            f"/{table}",
            json=data,
            headers=headers,
            params={"on_conflict": on_conflict} if on_conflict else {},
        )
        resp.raise_for_status()
        result = resp.json()
        return result[0] if isinstance(data, dict) else result
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()


# Global client instance
_db: Optional[SupabaseClient] = None

def get_db() -> SupabaseClient:
    """Get or create database client."""
    global _db
    if _db is None:
        _db = SupabaseClient()
    return _db


# ── API Key Management ───────────────────────────────────────────────

def validate_api_key(key: str) -> Optional[dict]:
    """
    Validate API key and return user + plan info.
    
    Returns:
        dict with {id, user_id, key, plan, rate_limit_per_hour, max_batch_size, name}
        or None if invalid/inactive
    """
    db = get_db()
    
    try:
        results = db.query("ck_api_keys", key=key, is_active=True)
        if not results:
            return None
        
        key_data = results[0]
        
        # Update last_used_at
        db.update("ck_api_keys", {"last_used_at": datetime.utcnow().isoformat()}, id=key_data["id"])
        
        return {
            "id": key_data["id"],
            "user_id": key_data["user_id"],
            "key": key_data["key"],
            "plan": key_data["plan"],
            "rate_limit_per_hour": key_data["rate_limit_per_hour"],
            "max_batch_size": key_data["max_batch_size"],
            "name": key_data.get("name", ""),
        }
    
    except Exception as e:
        print(f"Error validating API key: {e}")
        return None


def create_api_key(user_id: str, name: str = "Default", plan: str = "free") -> str:
    """
    Create a new API key for a user.
    
    Returns:
        The generated API key (format: ck_{plan}_{hex})
    """
    db = get_db()
    
    # Rate limits based on plan
    limits = {
        "free": {"rate_limit_per_hour": 20, "max_batch_size": 5},
        "starter": {"rate_limit_per_hour": 200, "max_batch_size": 50},
        "pro": {"rate_limit_per_hour": 2000, "max_batch_size": 500},
        "enterprise": {"rate_limit_per_hour": 50000, "max_batch_size": 5000},
    }
    
    limit_config = limits.get(plan, limits["free"])
    
    # Generate unique key
    key = f"ck_{plan}_{secrets.token_hex(16)}"
    
    key_data = {
        "user_id": user_id,
        "key": key,
        "name": name,
        "plan": plan,
        "rate_limit_per_hour": limit_config["rate_limit_per_hour"],
        "max_batch_size": limit_config["max_batch_size"],
        "is_active": True,
    }
    
    db.insert("ck_api_keys", key_data)
    return key


# ── Usage Tracking ────────────────────────────────────────────────────

def log_usage(
    api_key_id: str,
    endpoint: str,
    url: Optional[str] = None,
    parser_used: Optional[str] = None,
    content_type: Optional[str] = None,
    content_length: int = 0,
    chunks_count: int = 0,
    crawl_time_ms: int = 0,
    success: bool = True,
    error: Optional[str] = None,
):
    """Log API usage event."""
    db = get_db()
    
    usage_data = {
        "api_key_id": api_key_id,
        "endpoint": endpoint,
        "url": url,
        "parser_used": parser_used,
        "content_type": content_type,
        "content_length": content_length,
        "chunks_count": chunks_count,
        "crawl_time_ms": crawl_time_ms,
        "success": success,
        "error": error,
        "created_at": datetime.utcnow().isoformat(),
    }
    
    try:
        db.insert("ck_usage", usage_data)
    except Exception as e:
        print(f"Error logging usage: {e}")


def get_usage(api_key_id: str, days: int = 30) -> dict:
    """Get usage statistics for an API key."""
    db = get_db()
    
    try:
        # Get recent usage
        since = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        # Note: Supabase REST API doesn't support aggregations directly
        # We'll fetch raw data and aggregate in Python
        usage_rows = db.client.get(
            "/ck_usage",
            params={
                "api_key_id": f"eq.{api_key_id}",
                "created_at": f"gte.{since}",
                "select": "success,content_length,chunks_count",
            },
        ).json()
        
        total_requests = len(usage_rows)
        successful = sum(1 for r in usage_rows if r.get("success"))
        failed = total_requests - successful
        total_chars = sum(r.get("content_length", 0) for r in usage_rows)
        total_chunks = sum(r.get("chunks_count", 0) for r in usage_rows)
        
        return {
            "api_key_id": api_key_id,
            "days": days,
            "total_requests": total_requests,
            "successful_requests": successful,
            "failed_requests": failed,
            "total_chars": total_chars,
            "total_chunks": total_chunks,
        }
    
    except Exception as e:
        print(f"Error getting usage: {e}")
        return {
            "api_key_id": api_key_id,
            "days": days,
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_chars": 0,
            "total_chunks": 0,
        }


def update_monthly_usage(api_key_id: str):
    """Update monthly usage summary (called periodically or after each request)."""
    db = get_db()
    
    try:
        # Get current month
        month = date.today().replace(day=1).isoformat()
        
        # Get this month's usage
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0).isoformat()
        
        usage_rows = db.client.get(
            "/ck_usage",
            params={
                "api_key_id": f"eq.{api_key_id}",
                "created_at": f"gte.{month_start}",
                "select": "success,content_length,chunks_count",
            },
        ).json()
        
        total_requests = len(usage_rows)
        successful = sum(1 for r in usage_rows if r.get("success"))
        failed = total_requests - successful
        total_chars = sum(r.get("content_length", 0) for r in usage_rows)
        total_chunks = sum(r.get("chunks_count", 0) for r in usage_rows)
        
        summary = {
            "api_key_id": api_key_id,
            "month": month,
            "total_requests": total_requests,
            "total_chars": total_chars,
            "total_chunks": total_chunks,
            "successful_requests": successful,
            "failed_requests": failed,
        }
        
        # Upsert monthly summary
        db.upsert("ck_usage_monthly", summary, on_conflict="api_key_id,month")
    
    except Exception as e:
        print(f"Error updating monthly usage: {e}")


# ── User Management ──────────────────────────────────────────────────

def create_user(email: str, name: str, password: str, plan: str = "free") -> dict:
    """
    Create a new user with hashed password.
    
    Returns:
        User data dict with {id, email, name, plan, created_at}
    """
    db = get_db()
    
    # Hash password with bcrypt
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    user_data = {
        "email": email,
        "name": name,
        "password_hash": password_hash,
        "plan": plan,
    }
    
    user = db.insert("ck_users", user_data)
    
    # Don't return password_hash
    user.pop("password_hash", None)
    return user


def authenticate(email: str, password: str) -> Optional[dict]:
    """
    Authenticate user by email and password.
    
    Returns:
        User data dict (without password_hash) or None if invalid
    """
    db = get_db()
    
    try:
        results = db.query("ck_users", email=email)
        if not results:
            return None
        
        user = results[0]
        password_hash = user.get("password_hash", "")
        
        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
            return None
        
        # Return user without password_hash
        user.pop("password_hash", None)
        return user
    
    except Exception as e:
        print(f"Error authenticating user: {e}")
        return None


def get_user_by_id(user_id: str) -> Optional[dict]:
    """Get user by ID (without password_hash)."""
    db = get_db()
    
    try:
        results = db.query("ck_users", id=user_id)
        if not results:
            return None
        
        user = results[0]
        user.pop("password_hash", None)
        return user
    
    except Exception as e:
        print(f"Error getting user: {e}")
        return None


def get_user_api_keys(user_id: str) -> list[dict]:
    """Get all API keys for a user."""
    db = get_db()
    
    try:
        keys = db.query("ck_api_keys", user_id=user_id)
        # Remove sensitive fields if needed
        return keys
    
    except Exception as e:
        print(f"Error getting user API keys: {e}")
        return []


# ── Admin Functions ──────────────────────────────────────────────────

def get_all_users() -> list[dict]:
    """Get all users (admin only)."""
    db = get_db()
    try:
        users = db.client.get("/ck_users", params={"select": "*"}).json()
        # Remove password hashes
        for user in users:
            user.pop("password_hash", None)
        return users
    except Exception as e:
        print(f"Error getting all users: {e}")
        return []


def get_all_api_keys() -> list[dict]:
    """Get all API keys with user info (admin only)."""
    db = get_db()
    try:
        # Join with users table
        keys = db.client.get(
            "/ck_api_keys",
            params={"select": "*, ck_users!inner(email, name)"}
        ).json()
        return keys
    except Exception as e:
        print(f"Error getting all API keys: {e}")
        return []


def toggle_api_key(key_id: str, active: bool) -> bool:
    """Toggle API key active status (admin only)."""
    db = get_db()
    try:
        db.update("ck_api_keys", {"is_active": active}, id=key_id)
        return True
    except Exception as e:
        print(f"Error toggling API key: {e}")
        return False


def get_aggregated_usage(days: int = 30) -> dict:
    """Get aggregated usage stats across all keys (admin only)."""
    db = get_db()
    try:
        since = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        usage_rows = db.client.get(
            "/ck_usage",
            params={
                "created_at": f"gte.{since}",
                "select": "api_key_id,success,content_length,chunks_count",
            },
        ).json()
        
        total_requests = len(usage_rows)
        successful = sum(1 for r in usage_rows if r.get("success"))
        total_chars = sum(r.get("content_length", 0) for r in usage_rows)
        total_chunks = sum(r.get("chunks_count", 0) for r in usage_rows)
        
        # Count by user
        by_user = {}
        for row in usage_rows:
            key_id = row["api_key_id"]
            if key_id not in by_user:
                by_user[key_id] = 0
            by_user[key_id] += 1
        
        top_users = sorted(by_user.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "days": days,
            "total_requests": total_requests,
            "successful_requests": successful,
            "failed_requests": total_requests - successful,
            "total_chars": total_chars,
            "total_chunks": total_chunks,
            "top_users": [{"api_key_id": k, "requests": v} for k, v in top_users],
        }
    except Exception as e:
        print(f"Error getting aggregated usage: {e}")
        return {}


# ── Payment Functions ────────────────────────────────────────────────

def create_payment_request(user_id: str, plan: str, amount_vnd: int, memo: str) -> dict:
    """Create a payment request."""
    db = get_db()
    data = {
        "user_id": user_id,
        "plan_requested": plan,
        "amount_vnd": amount_vnd,
        "memo": memo,
        "status": "pending",
    }
    return db.insert("ck_payment_requests", data)


def get_payment_requests(user_id: Optional[str] = None, status: str = "pending") -> list[dict]:
    """Get payment requests (optionally filtered by user_id and status)."""
    db = get_db()
    try:
        params = {"select": "*, ck_users!inner(email, name)"}
        if status:
            params["status"] = f"eq.{status}"
        if user_id:
            params["user_id"] = f"eq.{user_id}"
        
        return db.client.get("/ck_payment_requests", params=params).json()
    except Exception as e:
        print(f"Error getting payment requests: {e}")
        return []


def confirm_payment(payment_id: str, confirmed_by: str) -> bool:
    """Confirm a payment request and upgrade user plan."""
    db = get_db()
    try:
        # Get payment request
        payments = db.query("ck_payment_requests", id=payment_id)
        if not payments:
            return False
        
        payment = payments[0]
        user_id = payment["user_id"]
        new_plan = payment["plan_requested"]
        
        # Update payment status
        db.update(
            "ck_payment_requests",
            {
                "status": "confirmed",
                "confirmed_at": datetime.utcnow().isoformat(),
                "confirmed_by": confirmed_by,
            },
            id=payment_id,
        )
        
        # Update user plan
        db.update("ck_users", {"plan": new_plan}, id=user_id)
        
        # Update all user's API keys to new plan
        keys = db.query("ck_api_keys", user_id=user_id)
        for key in keys:
            # Get new rate limits
            limits = {
                "free": {"rate_limit_per_hour": 20, "max_batch_size": 5},
                "starter": {"rate_limit_per_hour": 200, "max_batch_size": 50},
                "pro": {"rate_limit_per_hour": 2000, "max_batch_size": 500},
                "enterprise": {"rate_limit_per_hour": 50000, "max_batch_size": 5000},
            }
            limit_config = limits.get(new_plan, limits["free"])
            
            db.update(
                "ck_api_keys",
                {
                    "plan": new_plan,
                    "rate_limit_per_hour": limit_config["rate_limit_per_hour"],
                    "max_batch_size": limit_config["max_batch_size"],
                },
                id=key["id"],
            )
        
        return True
    except Exception as e:
        print(f"Error confirming payment: {e}")
        return False


def reject_payment(payment_id: str) -> bool:
    """Reject a payment request."""
    db = get_db()
    try:
        db.update("ck_payment_requests", {"status": "rejected"}, id=payment_id)
        return True
    except Exception as e:
        print(f"Error rejecting payment: {e}")
        return False


# ── Settings Functions ───────────────────────────────────────────────

def get_setting(key: str) -> Optional[str]:
    """Get a setting value."""
    db = get_db()
    try:
        results = db.query("ck_settings", key=key)
        if results:
            return results[0]["value"]
        return None
    except Exception as e:
        print(f"Error getting setting {key}: {e}")
        return None


def get_all_settings() -> dict:
    """Get all settings as a dict."""
    db = get_db()
    try:
        settings = db.client.get("/ck_settings", params={"select": "*"}).json()
        return {s["key"]: s["value"] for s in settings}
    except Exception as e:
        print(f"Error getting all settings: {e}")
        return {}


def update_setting(key: str, value: str) -> bool:
    """Update a setting (creates if doesn't exist)."""
    db = get_db()
    try:
        db.upsert("ck_settings", {"key": key, "value": value, "updated_at": datetime.utcnow().isoformat()})
        return True
    except Exception as e:
        print(f"Error updating setting {key}: {e}")
        return False
