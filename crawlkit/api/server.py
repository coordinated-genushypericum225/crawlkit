"""
CrawlKit API Server — FastAPI-based web API.

Endpoints:
    POST /v1/scrape          — Scrape a single URL
    POST /v1/batch           — Batch scrape multiple URLs
    POST /v1/discover        — Discover URLs from a source
    GET  /v1/parsers         — List available parsers
    GET  /v1/health          — Health check
    GET  /                   — Landing page
"""

from __future__ import annotations
import os
import time
import hashlib
import secrets
import ipaddress
import socket
import asyncio
from typing import Optional, Literal
from datetime import datetime
from collections import defaultdict
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Header, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
import orjson

from ..core.crawler import CrawlKit
from .. import db

# ── Security Helpers ─────────────────────────────────────────────────

class RateLimiter:
    """Simple in-memory rate limiter."""
    def __init__(self):
        self._requests = defaultdict(list)  # key -> [timestamps]
    
    def check(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """Return True if request is allowed."""
        now = time.time()
        # Clean old requests outside window
        self._requests[key] = [t for t in self._requests[key] if t > now - window_seconds]
        if len(self._requests[key]) >= max_requests:
            return False
        self._requests[key].append(now)
        return True

rate_limiter = RateLimiter()

# SSRF Protection
BLOCKED_HOSTS = {'localhost', '127.0.0.1', '0.0.0.0', '::1', 'metadata.google.internal'}
BLOCKED_RANGES = [
    ipaddress.ip_network('127.0.0.0/8'),      # Loopback
    ipaddress.ip_network('10.0.0.0/8'),        # Private
    ipaddress.ip_network('172.16.0.0/12'),     # Private
    ipaddress.ip_network('192.168.0.0/16'),    # Private
    ipaddress.ip_network('169.254.0.0/16'),    # Link-local (AWS metadata)
    ipaddress.ip_network('::1/128'),           # IPv6 loopback
    ipaddress.ip_network('fc00::/7'),          # IPv6 private
]

def validate_url(url: str) -> str:
    """Validate URL is safe to fetch. Raises ValueError if not."""
    parsed = urlparse(url)
    
    # Must be http or https
    if parsed.scheme not in ('http', 'https'):
        raise ValueError(f"Invalid URL scheme: {parsed.scheme}. Only http/https allowed.")
    
    # Check blocked hostnames
    hostname = parsed.hostname or ''
    if hostname.lower() in BLOCKED_HOSTS:
        raise ValueError("Access to internal hosts is not allowed.")
    
    # Resolve hostname and check IP
    try:
        ip = socket.gethostbyname(hostname)
        ip_addr = ipaddress.ip_address(ip)
        for network in BLOCKED_RANGES:
            if ip_addr in network:
                raise ValueError("Access to internal/private networks is not allowed.")
    except socket.gaierror:
        pass  # Let the fetcher handle DNS resolution errors
    
    # Check for decimal IP bypass (http://2130706433)
    try:
        ip_addr = ipaddress.ip_address(hostname)
        for network in BLOCKED_RANGES:
            if ip_addr in network:
                raise ValueError("Access to internal/private networks is not allowed.")
    except ValueError:
        pass  # Not an IP, that's fine
    
    return url

def get_client_ip(request: Request) -> str:
    """Get client IP from request, handling proxies."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

# ── App ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="CrawlKit API",
    description="Web + Video Intelligence API for AI — Crawl, parse, and structure web data for AI",
    version="0.1.0",
    docs_url="/docs",
    redoc_url=None,
)


# Entry point for Railway / production
def start():
    """Start the server — reads PORT from env."""
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://crawlkit.org",
        "https://www.crawlkit.org",
        "https://crawlkit.vercel.app",
        "http://localhost:3000",  # Dev only
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Global exception handler to hide error details in production
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal server error"}
    )

# Background task for periodic cleanup
@app.on_event("startup")
async def start_cleanup_task():
    """Run periodic cleanup every 5 minutes."""
    async def periodic_cleanup():
        while True:
            await asyncio.sleep(300)  # 5 minutes
            try:
                await cleanup_expired_device_sessions()
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Device session cleanup failed: {e}")
    
    asyncio.create_task(periodic_cleanup())

# ── State ────────────────────────────────────────────────────────────

# Initialize learning engine if Supabase is configured
learning_engine = None
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if SUPABASE_URL and SUPABASE_KEY:
    try:
        from ..intelligence import PatternStorage, LearningEngine
        storage = PatternStorage(supabase_url=SUPABASE_URL, supabase_key=SUPABASE_KEY)
        learning_engine = LearningEngine(storage=storage)
        print(f"✅ Learning engine initialized with Supabase storage")
    except Exception as e:
        print(f"⚠️ Learning engine init failed: {e}")
        learning_engine = None
else:
    print("ℹ️ Learning engine disabled (set SUPABASE_URL and SUPABASE_SERVICE_KEY to enable)")

crawler = CrawlKit(learning_engine=learning_engine)

# Master key for admin access (bypasses database)
MASTER_KEY = os.getenv("CRAWLKIT_MASTER_KEY", "ck_master_dev")

# Rate limits per plan (for reference)
RATE_LIMITS = {
    "free": {"requests_per_hour": 20, "max_batch": 5},
    "starter": {"requests_per_hour": 200, "max_batch": 50},
    "pro": {"requests_per_hour": 2000, "max_batch": 500},
    "enterprise": {"requests_per_hour": 50000, "max_batch": 5000},
}

# Device Flow OAuth sessions (in-memory with thread-safety)

class DeviceSessionStore:
    def __init__(self):
        self._sessions = {}
        self._lock = asyncio.Lock()
    
    async def create(self, device_code: str, session_data: dict):
        async with self._lock:
            self._sessions[device_code] = session_data
    
    async def get(self, device_code: str) -> Optional[dict]:
        async with self._lock:
            return self._sessions.get(device_code)
    
    async def update(self, device_code: str, **kwargs) -> bool:
        async with self._lock:
            if device_code in self._sessions:
                self._sessions[device_code].update(kwargs)
                return True
            return False
    
    async def delete(self, device_code: str) -> bool:
        async with self._lock:
            if device_code in self._sessions:
                del self._sessions[device_code]
                return True
            return False
    
    async def cleanup(self):
        """Remove expired sessions."""
        async with self._lock:
            now = time.time()
            expired = [k for k, v in self._sessions.items() if now > v.get("expires_at", 0)]
            for k in expired:
                del self._sessions[k]
            if expired:
                print(f"🗑️ Cleaned up {len(expired)} expired device sessions")
    
    async def find_by_user_code(self, user_code: str) -> tuple[Optional[str], Optional[dict]]:
        async with self._lock:
            for code, session in self._sessions.items():
                if session.get("user_code") == user_code and session.get("status") == "pending":
                    return code, session
            return None, None

device_store = DeviceSessionStore()

async def cleanup_expired_device_sessions():
    """Remove expired device sessions (run periodically)."""
    await device_store.cleanup()


# ── Models ───────────────────────────────────────────────────────────

class ScrapeRequest(BaseModel):
    url: str
    parser: Optional[str] = None
    format: str = "markdown"  # text | markdown | html_clean
    formats: Optional[list[str]] = None  # Legacy support (deprecated)
    chunk: bool = True
    chunk_max_tokens: int = 512
    force_js: bool = False
    include_html: bool = False
    intelligence: bool = False  # Enable video intelligence analysis
    lang: Optional[str] = None  # Preferred subtitle language (for video)
    auto_extract: bool = False  # Use adaptive content extraction (universal parser)
    # New features
    nlp: bool = False  # Enable NLP extraction (entities, keywords)
    ocr: bool = False  # Enable OCR for scanned PDFs
    stealth: bool = False  # Enable anti-bot stealth mode
    screenshot: bool = False  # Capture screenshot
    
    @field_validator('url')
    def validate_url_field(cls, v):
        if not v or not v.strip():
            raise ValueError("URL cannot be empty")
        if len(v) > 2048:
            raise ValueError("URL too long (max 2048 characters)")
        if not v.startswith('http://') and not v.startswith('https://'):
            raise ValueError("URL must start with http:// or https://")
        return v.strip()

class BatchRequest(BaseModel):
    urls: list[str] = Field(..., max_length=500)
    parser: Optional[str] = None
    format: str = "markdown"  # text | markdown | html_clean
    chunk: bool = True
    delay: float = 1.5

class DiscoverRequest(BaseModel):
    source: Optional[str] = None
    url: Optional[str] = None  # Alias for source (for consistency with /v1/scrape)
    query: Optional[str] = None
    limit: int = Field(default=100, le=1000)
    
    def get_source(self) -> str:
        """Get source from either url or source field."""
        if self.url:
            return self.url
        if self.source:
            return self.source
        raise ValueError("Either 'url' or 'source' field is required")


# ── Auth ─────────────────────────────────────────────────────────────

def _get_api_key(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """Extract API key from header."""
    if not authorization:
        return None
    if authorization.startswith("Bearer "):
        return authorization[7:]
    return authorization

def require_auth(authorization: Optional[str] = Header(None)) -> dict:
    """Require valid API key."""
    key = _get_api_key(authorization)
    if not key:
        raise HTTPException(401, "API key required. Set Authorization: Bearer <key>")
    
    if key == MASTER_KEY:
        return {"id": "master", "key": key, "plan": "enterprise", "name": "master", "max_batch_size": 5000}
    
    # Validate via database
    key_data = db.validate_api_key(key)
    if not key_data:
        raise HTTPException(401, "Invalid API key")
    
    return key_data

def optional_auth(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    """Optional API key (for free tier)."""
    key = _get_api_key(authorization)
    if not key:
        return {"id": "anonymous", "key": "anonymous", "plan": "free", "name": "anonymous", "max_batch_size": 5}
    if key == MASTER_KEY:
        return {"id": "master", "key": key, "plan": "enterprise", "name": "master", "max_batch_size": 5000}
    
    # Try database validation
    key_data = db.validate_api_key(key)
    return key_data if key_data else {"id": "unknown", "key": key, "plan": "free", "name": "unknown", "max_batch_size": 5}


# ── Endpoints ────────────────────────────────────────────────────────

@app.get("/v1/health")
async def health():
    return {
        "status": "ok",
        "version": "0.1.0",
        "parsers": list(crawler._parsers.keys()),
        "timestamp": datetime.now().isoformat(),
    }


# ── Auth helpers (forward declaration for learning endpoints) ────────

def require_admin_early(authorization: Optional[str] = Header(None)) -> str:
    """Verify admin/master key (early declaration)."""
    if not authorization:
        raise HTTPException(401, "Admin key required")
    key = authorization.replace("Bearer ", "")
    if key != MASTER_KEY:
        raise HTTPException(403, "Invalid admin key")
    return key

# ── Learning Engine Endpoints ────────────────────────────────────────

@app.get("/v1/admin/learning/stats")
async def admin_learning_stats(admin_key: str = Depends(require_admin_early)):
    """
    Get learning engine statistics (admin only).
    
    Shows how many patterns learned, quality scores, top domains, etc.
    """
    if not crawler.learning_engine:
        return {
            "status": "disabled",
            "message": "Learning engine not initialized. Set SUPABASE_URL and SUPABASE_KEY env vars."
        }
    
    try:
        stats = crawler.learning_engine.storage.get_stats()
        return {
            "success": True,
            "stats": stats,
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to get learning stats: {e}")


class FeedbackRequest(BaseModel):
    url: str
    feedback: str  # good | bad | missing_content | wrong_type
    details: Optional[str] = None


@app.post("/v1/feedback")
async def submit_feedback(req: FeedbackRequest, user: dict = Depends(require_auth)):
    """
    Submit extraction quality feedback.
    
    Helps improve the learning engine by reporting:
    - good: Extraction was perfect
    - bad: Extraction was wrong
    - missing_content: Some content was missed
    - wrong_type: Content type detection was wrong
    """
    if not crawler.learning_engine:
        raise HTTPException(503, "Learning engine not available")
    
    # Validate feedback type
    valid_types = ["good", "bad", "missing_content", "wrong_type"]
    if req.feedback not in valid_types:
        raise HTTPException(400, f"Invalid feedback type. Must be one of: {', '.join(valid_types)}")
    
    # Store feedback in DB
    try:
        from urllib.parse import urlparse
        domain = urlparse(req.url).netloc.lower().replace("www.", "")
        
        # Get API key ID if available
        api_key_id = user.get("id") if user.get("id") not in ["anonymous", "master"] else None
        
        # Insert feedback
        if crawler.learning_engine.storage._db:
            feedback_data = {
                "url": req.url,
                "domain": domain,
                "api_key_id": api_key_id,
                "feedback_type": req.feedback,
                "details": req.details,
            }
            crawler.learning_engine.storage._db.table("ck_extraction_feedback").insert(feedback_data).execute()
        
        return {
            "success": True,
            "message": "Thank you for your feedback! This helps improve extraction quality.",
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to submit feedback: {e}")


@app.get("/v1/parsers")
async def list_parsers():
    """List available domain parsers."""
    parsers = []
    for name, p in crawler._parsers.items():
        # Check if discover is actually implemented (not just inherited from base)
        supports_discovery = False
        if hasattr(p, "discover"):
            # Try to detect if it's overridden by checking the class, not base
            try:
                # If the method is defined in the parser's class (not BaseParser), it's implemented
                supports_discovery = "discover" in p.__class__.__dict__
            except:
                supports_discovery = False
        
        parsers.append({
            "name": name,
            "domain": p.domain,
            "supports_discovery": supports_discovery,
        })
    return {"parsers": parsers}


@app.post("/v1/scrape")
async def scrape(req: ScrapeRequest, request: Request, user: dict = Depends(require_auth)):
    """
    Scrape a single URL and return structured data.
    
    Returns content in the specified format (markdown, text, or html_clean) with structured data and RAG-ready chunks.
    """
    start = time.time()
    
    # SSRF protection
    try:
        validate_url(req.url)
    except ValueError as e:
        raise HTTPException(400, str(e))
    
    # Rate limiting based on plan
    plan = user.get('plan', 'free')
    rate_limits_per_min = {'free': 10, 'starter': 60, 'pro': 300, 'enterprise': 10000}
    max_requests = rate_limits_per_min.get(plan, 10)
    
    client_ip = get_client_ip(request)
    if not rate_limiter.check(f"scrape:{user.get('id', client_ip)}", max_requests, 60):
        raise HTTPException(429, "Too many requests. Try again later.")
    
    # Use new format parameter if provided, otherwise fall back to formats list
    if req.formats is not None:
        # Legacy formats list support
        output_format = req.formats[0] if req.formats else "markdown"
    else:
        # New single format parameter
        output_format = req.format
    
    result = await crawler.scrape(
        url=req.url,
        parser=req.parser,
        format=output_format,
        chunk=req.chunk,
        chunk_max_tokens=req.chunk_max_tokens,
        force_js=req.force_js,
        lang=req.lang,
        intelligence=req.intelligence,
        auto_extract=req.auto_extract,
        nlp=req.nlp,
        ocr=req.ocr,
        stealth=req.stealth,
        screenshot=req.screenshot,
    )
    
    # Log usage to database
    if user.get("id") and user["id"] not in ["anonymous", "master"]:
        db.log_usage(
            api_key_id=user["id"],
            endpoint="/v1/scrape",
            url=req.url,
            parser_used=result.parser_used,
            content_type=result.content_type,
            content_length=result.content_length,
            chunks_count=len(result.chunks) if result.chunks else 0,
            crawl_time_ms=result.crawl_time_ms,
            success=result.success,
            error=result.error,
        )
    
    if result.error:
        return JSONResponse(
            status_code=422,
            content={"success": False, "error": result.error},
        )
    
    # Get the formatted content based on output format
    if output_format == "markdown":
        content = result.markdown
    elif output_format == "text":
        content = result.text
    elif output_format == "html_clean":
        content = result.html
    else:
        content = result.markdown  # Default to markdown
    
    response = {
        "success": True,
        "data": {
            "url": result.url,
            "final_url": result.final_url,
            "title": result.title,
            "content": content,  # Single content field based on format
            "format": output_format,  # Include format in response
            "content_type": result.content_type,
            "parser_used": result.parser_used,
            "content_length": len(content),
            "crawl_time_ms": result.crawl_time_ms,
            "rendered_js": result.rendered_js,
        },
    }
    
    # Legacy support - include markdown/text/html if requested via formats list
    if req.formats is not None:
        if "markdown" in req.formats:
            response["data"]["markdown"] = result.markdown
        if "text" in req.formats:
            response["data"]["text"] = result.text
        if "html" in req.formats or req.include_html:
            response["data"]["html"] = result.html
    
    if result.structured:
        response["data"]["structured"] = result.structured
    if result.metadata:
        response["data"]["metadata"] = result.metadata
    if result.chunks:
        response["data"]["chunks"] = result.chunks
        response["data"]["chunks_count"] = len(result.chunks)
    
    # Add NLP results if available
    if req.nlp and (result.entities or result.keywords):
        response["data"]["nlp"] = {
            "entities": result.entities,
            "keywords": result.keywords,
            "language": result.language,
        }
    
    return response


@app.post("/v1/batch")
async def batch_scrape(req: BatchRequest, user: dict = Depends(require_auth)):
    """Batch scrape multiple URLs."""
    max_batch = user.get("max_batch_size", 5)
    
    if len(req.urls) > max_batch:
        raise HTTPException(
            400,
            f"Batch size {len(req.urls)} exceeds limit {max_batch} for {user.get('plan', 'free')} plan",
        )
    
    results = await crawler.batch_scrape(
        urls=req.urls,
        parser=req.parser,
        format=req.format,
        delay=req.delay,
    )
    
    # Log each result to database
    if user.get("id") and user["id"] not in ["anonymous", "master"]:
        for r in results:
            db.log_usage(
                api_key_id=user["id"],
                endpoint="/v1/batch",
                url=r.url,
                parser_used=r.parser_used,
                content_type=r.content_type,
                content_length=r.content_length,
                chunks_count=len(r.chunks) if r.chunks else 0,
                crawl_time_ms=r.crawl_time_ms,
                success=r.success,
                error=r.error,
            )
    
    return {
        "success": True,
        "total": len(results),
        "successful": sum(1 for r in results if r.success),
        "data": [
            {
                "url": r.url,
                "title": r.title,
                "content_type": r.content_type,
                "content_length": r.content_length,
                "chunks_count": len(r.chunks),
                "success": r.success,
                "error": r.error,
            }
            for r in results
        ],
    }


@app.post("/v1/discover")
async def discover(req: DiscoverRequest, user: dict = Depends(require_auth)):
    """Discover URLs from a source."""
    try:
        # Get source from either url or source field
        try:
            source = req.get_source()
        except ValueError as e:
            raise HTTPException(400, str(e))
        
        # Try to detect parser from URL if full URL is provided
        if source.startswith("http://") or source.startswith("https://"):
            from urllib.parse import urlparse
            domain = urlparse(source).netloc.replace("www.", "")
            # Map domain to parser name
            domain_map = {
                "thuvienphapluat.vn": "tvpl",
                "vbpl.vn": "vbpl",
                "vnexpress.net": "vnexpress",
                "batdongsan.com.vn": "batdongsan",
                "cafef.vn": "cafef",
                "youtube.com": "youtube",
                "youtu.be": "youtube",
                "tiktok.com": "tiktok",
                "facebook.com": "facebook_video",
            }
            source = domain_map.get(domain, source)
        
        urls = crawler.discover(source, query=req.query, limit=req.limit)
        
        # Log usage to database
        if user.get("id") and user["id"] not in ["anonymous", "master"]:
            db.log_usage(
                api_key_id=user["id"],
                endpoint="/v1/discover",
                url=req.url or req.source,
                content_length=0,
                chunks_count=len(urls),
                success=True,
            )
        
        return {"success": True, "count": len(urls), "urls": urls}
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Discovery failed: {e}")


# ── Auth Endpoints ───────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: str
    name: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class CreateKeyRequest(BaseModel):
    name: str = "Default"
    plan: str = "free"

class DeviceAuthRequest(BaseModel):
    client_name: str = "CrawlKit CLI"

class DevicePollRequest(BaseModel):
    device_code: str

class DeviceApproveRequest(BaseModel):
    user_code: str


@app.post("/v1/auth/register")
async def register(req: RegisterRequest, request: Request):
    """Register a new user and get a free API key."""
    # Rate limiting: 5 registrations per minute per IP
    client_ip = get_client_ip(request)
    if not rate_limiter.check(f"register:{client_ip}", 5, 60):
        raise HTTPException(429, "Too many registration attempts. Try again later.")
    
    try:
        # Create user
        user = db.create_user(email=req.email, name=req.name, password=req.password, plan="free")
        
        # Create default API key
        api_key = db.create_api_key(user_id=user["id"], name="Default", plan="free")
        
        return {
            "success": True,
            "user": user,
            "api_key": api_key,
            "message": "Registration successful. Use your API key to authenticate requests.",
        }
    
    except Exception as e:
        raise HTTPException(400, f"Registration failed: {e}")


@app.post("/v1/auth/login")
async def login(req: LoginRequest, request: Request):
    """Login and get user info + API keys."""
    # Rate limiting: 10 login attempts per minute per IP
    client_ip = get_client_ip(request)
    if not rate_limiter.check(f"login:{client_ip}", 10, 60):
        raise HTTPException(429, "Too many login attempts. Try again later.")
    
    user = db.authenticate(email=req.email, password=req.password)
    
    if not user:
        raise HTTPException(401, "Invalid email or password")
    
    # Get user's API keys
    api_keys = db.get_user_api_keys(user["id"])
    
    return {
        "success": True,
        "user": user,
        "api_keys": [k["key"] for k in api_keys if k.get("is_active")],
    }


@app.get("/v1/auth/me")
async def get_current_user(user: dict = Depends(require_auth)):
    """Get current user info from API key."""
    if user.get("id") in ["master", "anonymous"]:
        return {"user": user, "api_keys": []}
    
    user_data = db.get_user_by_id(user.get("user_id"))
    if not user_data:
        raise HTTPException(404, "User not found")
    
    # Get all API keys for this user
    all_keys = db.get_user_api_keys(user_data["id"])
    
    return {
        "user": user_data,
        "api_keys": all_keys,
        "api_key": {
            "name": user.get("name"),
            "plan": user.get("plan"),
            "rate_limit_per_hour": user.get("rate_limit_per_hour"),
            "max_batch_size": user.get("max_batch_size"),
        },
    }


@app.post("/v1/auth/keys")
async def create_user_api_key(req: CreateKeyRequest, request: Request, user: dict = Depends(require_auth)):
    """Create an additional API key for the current user."""
    if user.get("id") in ["master", "anonymous"]:
        raise HTTPException(403, "Anonymous users cannot create API keys")
    
    # Rate limiting: 5 key creations per hour per user
    if not rate_limiter.check(f"create_key:{user.get('id')}", 5, 3600):
        raise HTTPException(429, "Too many key creation requests. Try again later.")
    
    # Validate plan
    if req.plan not in ["free", "starter", "pro", "enterprise"]:
        raise HTTPException(400, "Invalid plan")
    
    # Only allow creating keys for own plan or lower
    user_data = db.get_user_by_id(user.get("user_id"))
    if not user_data:
        raise HTTPException(404, "User not found")
    
    # Check existing key count (MAX 20 active keys per user)
    MAX_KEYS_PER_USER = 20
    existing_keys = db.get_user_api_keys(user_data["id"])
    active_keys = [k for k in existing_keys if k.get('is_active', True)]
    if len(active_keys) >= MAX_KEYS_PER_USER:
        raise HTTPException(400, f"Maximum {MAX_KEYS_PER_USER} active API keys allowed per user.")
    
    api_key = db.create_api_key(
        user_id=user_data["id"],
        name=req.name,
        plan=req.plan,
    )
    
    return {"success": True, "api_key": api_key, "plan": req.plan}


@app.get("/v1/auth/usage")
async def get_user_usage(days: int = 30, user: dict = Depends(require_auth)):
    """Get usage stats for current user's API key."""
    if user.get("id") in ["master", "anonymous"]:
        return {"usage": {"total_requests": 0, "message": "Anonymous/master keys have no usage tracking"}}
    
    usage_stats = db.get_usage(user["id"], days=days)
    return {"usage": usage_stats}


# ── Device Flow OAuth ────────────────────────────────────────────────

@app.post("/v1/auth/device/start")
async def device_auth_start(req: DeviceAuthRequest, request: Request):
    """Start OAuth Device Flow — returns device_code + user_code for browser auth."""
    # Rate limiting: 10 device flow starts per minute per IP
    client_ip = get_client_ip(request)
    if not rate_limiter.check(f"device_start:{client_ip}", 10, 60):
        raise HTTPException(429, "Too many device auth attempts. Try again later.")
    
    # Cleanup old sessions periodically
    await cleanup_expired_device_sessions()
    
    # Generate codes
    device_code = secrets.token_hex(32)
    user_code = secrets.token_hex(4).upper()
    
    # Store session
    await device_store.create(device_code, {
        "user_code": user_code,
        "client_name": req.client_name,
        "created_at": time.time(),
        "expires_at": time.time() + 600,  # 10 minutes
        "status": "pending",  # pending → approved → used
        "api_key": None,
        "user_info": None,
        "last_poll": 0,  # For rate limiting polls
    })
    
    return {
        "device_code": device_code,
        "user_code": user_code,
        "verification_url": f"https://crawlkit.org/auth/device?code={user_code}",
        "expires_in": 600,
        "interval": 5,  # Poll every 5 seconds
    }


@app.post("/v1/auth/device/poll")
async def device_auth_poll(req: DevicePollRequest, request: Request):
    """Poll for device authorization status."""
    session = await device_store.get(req.device_code)
    
    if not session:
        raise HTTPException(404, "Device code not found or expired")
    
    # Check expiry
    if time.time() > session["expires_at"]:
        await device_store.delete(req.device_code)
        raise HTTPException(410, "Device code expired")
    
    # Rate limit: max 1 poll per 3 seconds per device_code
    now = time.time()
    if now - session.get("last_poll", 0) < 3:
        raise HTTPException(429, "Slow down. Poll interval is 5 seconds.")
    await device_store.update(req.device_code, last_poll=now)
    
    # Check status
    if session["status"] == "pending":
        return {"status": "pending"}
    
    if session["status"] == "approved":
        # One-time use - delete after returning
        api_key = session["api_key"]
        user_info = session["user_info"]
        await device_store.delete(req.device_code)
        
        return {
            "status": "approved",
            "api_key": api_key,
            "user": user_info,
        }
    
    raise HTTPException(400, "Device code already used or invalid")


@app.post("/v1/auth/device/approve")
async def device_auth_approve(req: DeviceApproveRequest, request: Request, user: dict = Depends(require_auth)):
    """Approve a device authorization request (called from web frontend)."""
    if user.get("id") in ["master", "anonymous"]:
        raise HTTPException(403, "Anonymous users cannot approve device auth")
    
    # Rate limiting: max 10 approve attempts per minute per user
    if not rate_limiter.check(f"device_approve:{user.get('id')}", 10, 60):
        raise HTTPException(429, "Too many approval attempts. Try again later.")
    
    # Find session by user_code
    device_code, session = await device_store.find_by_user_code(req.user_code)
    
    if not device_code or not session:
        raise HTTPException(404, "Invalid or expired user code")
    
    # Create new API key for the CLI
    user_data = db.get_user_by_id(user.get("user_id"))
    if not user_data:
        raise HTTPException(404, "User not found")
    
    api_key = db.create_api_key(
        user_id=user_data["id"],
        name=f"CLI - {session['client_name']}",
        plan=user_data.get("plan", "free")
    )
    
    # Update session
    await device_store.update(device_code,
        status="approved",
        api_key=api_key,
        user_info={
            "email": user_data.get("email"),
            "name": user_data.get("name"),
            "plan": user_data.get("plan", "free"),
        }
    )
    
    return {
        "success": True,
        "message": "Device authorized successfully",
        "client_name": session["client_name"],
    }


# ── Admin Endpoints ──────────────────────────────────────────────────

def require_admin(authorization: Optional[str] = Header(None)) -> str:
    """Require master key for admin access."""
    key = _get_api_key(authorization)
    if key != MASTER_KEY:
        raise HTTPException(403, "Admin access required (master key)")
    return key


@app.post("/v1/admin/verify")
async def admin_verify(request: Request, admin_key: str = Depends(require_admin)):
    """Verify admin/master key (for frontend login)."""
    # Rate limiting: 5 admin verify attempts per minute per IP
    client_ip = get_client_ip(request)
    if not rate_limiter.check(f"admin_verify:{client_ip}", 5, 60):
        raise HTTPException(429, "Too many attempts. Try again later.")
    
    return {"success": True, "message": "Valid master key"}


@app.get("/v1/admin/users")
async def admin_list_users(admin_key: str = Depends(require_admin)):
    """List all users (admin only)."""
    users = db.get_all_users()
    return users


@app.get("/v1/admin/keys")
async def admin_list_keys(admin_key: str = Depends(require_admin)):
    """List all API keys with user info (admin only)."""
    keys = db.get_all_api_keys()
    # Add user_email to top level for frontend compatibility
    for key in keys:
        if "ck_users" in key:
            key["user_email"] = key["ck_users"].get("email", "")
    return keys


@app.delete("/v1/auth/keys/{key_id}")
async def revoke_user_api_key(key_id: str, user: dict = Depends(require_auth)):
    """Revoke (deactivate) an API key."""
    if user.get("id") in ["master", "anonymous"]:
        raise HTTPException(403, "Anonymous users cannot revoke keys")
    
    # Check if key belongs to user
    user_data = db.get_user_by_id(user.get("user_id"))
    if not user_data:
        raise HTTPException(404, "User not found")
    
    user_keys = db.get_user_api_keys(user_data["id"])
    key_ids = [k["id"] for k in user_keys]
    
    if key_id not in key_ids:
        raise HTTPException(403, "You can only revoke your own keys")
    
    success = db.toggle_api_key(key_id, False)
    if not success:
        raise HTTPException(404, "Key not found")
    
    return {"success": True, "message": "API key revoked"}


@app.post("/v1/admin/keys/{key_id}/toggle")
async def admin_toggle_key(
    key_id: str,
    active: bool,
    admin_key: str = Depends(require_admin)
):
    """Toggle API key active status (admin only)."""
    success = db.toggle_api_key(key_id, active)
    if not success:
        raise HTTPException(404, "Key not found")
    return {"success": True, "key_id": key_id, "active": active}


@app.get("/v1/admin/usage")
async def admin_get_usage(
    days: int = 30,
    admin_key: str = Depends(require_admin)
):
    """Get aggregated usage stats (admin only)."""
    stats = db.get_aggregated_usage(days)
    return stats


@app.get("/v1/admin/stats")
async def admin_get_stats(admin_key: str = Depends(require_admin)):
    """Get admin dashboard stats (admin only)."""
    users = db.get_all_users()
    keys = db.get_all_api_keys()
    usage_stats = db.get_aggregated_usage(1)  # Today
    usage_all = db.get_aggregated_usage(30)  # 30 days
    
    return {
        "total_users": len(users),
        "total_keys": len(keys),
        "total_requests": usage_all.get("total_requests", 0),
        "today_requests": usage_stats.get("total_requests", 0),
    }


@app.get("/v1/admin/payments")
async def admin_list_payments(
    status: str = "pending",
    admin_key: str = Depends(require_admin)
):
    """List payment requests (admin only)."""
    payments = db.get_payment_requests(status=status)
    return payments


@app.post("/v1/admin/payments/{payment_id}/confirm")
async def admin_confirm_payment(
    payment_id: str,
    admin_key: str = Depends(require_admin)
):
    """Confirm a payment request (admin only)."""
    success = db.confirm_payment(payment_id, confirmed_by="admin")
    if not success:
        raise HTTPException(404, "Payment request not found")
    return {"success": True, "payment_id": payment_id, "status": "confirmed"}


@app.post("/v1/admin/payments/{payment_id}/reject")
async def admin_reject_payment(
    payment_id: str,
    admin_key: str = Depends(require_admin)
):
    """Reject a payment request (admin only)."""
    success = db.reject_payment(payment_id)
    if not success:
        raise HTTPException(404, "Payment request not found")
    return {"success": True, "payment_id": payment_id, "status": "rejected"}


@app.get("/v1/admin/settings")
async def admin_get_settings(admin_key: str = Depends(require_admin)):
    """Get all settings (admin only)."""
    settings = db.get_all_settings()
    return settings


@app.post("/v1/admin/settings")
async def admin_update_settings(
    settings: dict,
    admin_key: str = Depends(require_admin)
):
    """Update settings (admin only)."""
    for key, value in settings.items():
        db.update_setting(key, str(value))
    return {"success": True, "updated": list(settings.keys())}


# ── Payment Endpoints ────────────────────────────────────────────────

class PaymentRequest(BaseModel):
    plan: str
    amount_vnd: Optional[int] = None
    memo: Optional[str] = None

PLAN_PRICES = {"starter": 475000, "pro": 1975000}

@app.post("/v1/payment/request")
async def create_payment_request(req: PaymentRequest, user: dict = Depends(require_auth)):
    """Create a payment request for plan upgrade."""
    if user.get("id") in ["master", "anonymous"]:
        raise HTTPException(403, "Anonymous users cannot request upgrades")
    
    user_id = user.get("user_id")
    if not user_id:
        raise HTTPException(400, "User ID not found")
    
    # Auto-fill amount and memo if not provided
    amount = req.amount_vnd or PLAN_PRICES.get(req.plan, 0)
    memo = req.memo or f"CrawlKit {req.plan} - {user_id[:8]}"
    
    if amount == 0:
        raise HTTPException(400, f"Invalid plan: {req.plan}. Valid plans: starter, pro")
    
    payment = db.create_payment_request(
        user_id=user_id,
        plan=req.plan,
        amount_vnd=amount,
        memo=memo
    )
    
    return {"success": True, "payment": payment}


@app.get("/v1/payment/status")
async def get_payment_status(user: dict = Depends(require_auth)):
    """Get current user's payment request status."""
    if user.get("id") in ["master", "anonymous"]:
        return {"payments": []}
    
    user_id = user.get("user_id")
    payments = db.get_payment_requests(user_id=user_id)
    
    return {"payments": payments}


@app.get("/v1/settings")
async def get_public_settings():
    """Get public settings (pricing, bank info for QR)."""
    settings = db.get_all_settings()
    # Only return public settings
    public_keys = ["bank_id", "bank_account", "bank_holder", "price_starter_vnd", "price_pro_vnd"]
    return {k: settings.get(k, "") for k in public_keys}


@app.post("/v1/admin/migrate")
async def run_migration(admin: dict = Depends(require_auth)):
    """
    Run database migration (admin/master key only).
    
    Executes schema.sql to create/update all tables.
    Safe to run multiple times (uses IF NOT EXISTS).
    """
    if admin.get("plan") != "enterprise":
        raise HTTPException(403, "Admin/master key required")
    
    try:
        import psycopg2
    except ImportError:
        raise HTTPException(500, "psycopg2 not installed. Run: pip install psycopg2-binary")
    
    # Get database URL
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        # Try to construct from Supabase config
        from urllib.parse import quote_plus
        supabase_url = os.getenv("SUPABASE_URL", "https://your-project.supabase.co")
        db_password = os.getenv("SUPABASE_DB_PASSWORD")
        
        if not db_password:
            raise HTTPException(
                500,
                "DATABASE_URL or SUPABASE_DB_PASSWORD not set. "
                "Get password from Supabase Dashboard → Settings → Database"
            )
        
        # Extract project ref from URL and URL-encode password for special chars
        project_ref = supabase_url.split("//")[1].split(".")[0]
        encoded_password = quote_plus(db_password)
        # Use Supavisor transaction pooler (IPv4, port 6543)
        # User format: postgres.{project_ref} for pooler auth
        db_url = f"postgres://postgres.{project_ref}:{encoded_password}@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"
    
    # Read schema.sql
    from pathlib import Path
    schema_path = Path(__file__).parent.parent.parent / "database" / "schema.sql"
    
    if not schema_path.exists():
        raise HTTPException(500, f"Schema file not found: {schema_path}")
    
    sql_content = schema_path.read_text()
    
    # Connect and execute
    try:
        # Parse URL to extract components
        from urllib.parse import urlparse
        import socket
        parsed = urlparse(db_url)
        
        # Resolve hostname to IPv4 address to avoid IPv6 issues
        host = parsed.hostname
        try:
            # Get IPv4 address
            addr_info = socket.getaddrinfo(host, parsed.port or 5432, socket.AF_INET, socket.SOCK_STREAM)
            if addr_info:
                ipv4_addr = addr_info[0][4][0]
                host = ipv4_addr
        except socket.gaierror:
            # Fall back to original hostname if resolution fails
            pass
        
        # Connect with explicit parameters
        from urllib.parse import unquote
        conn = psycopg2.connect(
            host=host,
            port=parsed.port or 5432,
            database=parsed.path.lstrip('/').split('?')[0],
            user=unquote(parsed.username) if parsed.username else 'postgres',
            password=unquote(parsed.password) if parsed.password else '',
            connect_timeout=15,
            sslmode='require',
            options='-c search_path=public'
        )
        with conn.cursor() as cur:
            # Split and execute statements
            statements = [s.strip() for s in sql_content.split(';') if s.strip()]
            executed = 0
            
            for statement in statements:
                if not statement:
                    continue
                cur.execute(statement)
                executed += 1
            
            conn.commit()
        
        conn.close()
        
        return {
            "success": True,
            "message": "Migration completed successfully",
            "statements_executed": executed,
        }
    
    except psycopg2.Error as e:
        raise HTTPException(500, f"Database error: {e}")
    except Exception as e:
        raise HTTPException(500, f"Migration failed: {e}")


# ── Watch Endpoints ──────────────────────────────────────────────────

class WatchRequest(BaseModel):
    url: str
    webhook_url: Optional[str] = None
    check_interval_minutes: int = 60
    selector: Optional[str] = None


@app.post("/v1/watch")
async def create_watch(req: WatchRequest, user: dict = Depends(require_auth)):
    """
    Register a URL to monitor for changes.
    
    Args:
        url: URL to watch
        webhook_url: Callback URL when change detected (optional)
        check_interval_minutes: How often to check (default 60)
        selector: CSS selector to monitor specific element (optional)
    
    Returns:
        Created watch record
    """
    if user.get("id") in ["master", "anonymous"]:
        raise HTTPException(403, "Anonymous users cannot create watches")
    
    try:
        from ..core.watch import get_watch_manager
        watch_mgr = get_watch_manager()
        
        watch = watch_mgr.create_watch(
            url=req.url,
            api_key_id=user["id"],
            webhook_url=req.webhook_url,
            check_interval_minutes=req.check_interval_minutes,
            selector=req.selector,
        )
        
        return {
            "success": True,
            "watch": watch,
        }
    
    except Exception as e:
        raise HTTPException(500, f"Failed to create watch: {e}")


@app.get("/v1/watch/list")
async def list_watches(user: dict = Depends(require_auth)):
    """
    List all active watches for current API key.
    
    Returns:
        List of watch records
    """
    if user.get("id") in ["master", "anonymous"]:
        return {"watches": []}
    
    try:
        from ..core.watch import get_watch_manager
        watch_mgr = get_watch_manager()
        
        watches = watch_mgr.get_watches(user["id"])
        
        return {
            "success": True,
            "count": len(watches),
            "watches": watches,
        }
    
    except Exception as e:
        raise HTTPException(500, f"Failed to list watches: {e}")


@app.delete("/v1/watch/{watch_id}")
async def remove_watch(watch_id: str, user: dict = Depends(require_auth)):
    """
    Remove a watch.
    
    Args:
        watch_id: Watch ID to remove
    
    Returns:
        Success status
    """
    if user.get("id") in ["master", "anonymous"]:
        raise HTTPException(403, "Anonymous users cannot remove watches")
    
    try:
        from ..core.watch import get_watch_manager
        watch_mgr = get_watch_manager()
        
        success = watch_mgr.remove_watch(watch_id, user["id"])
        
        if not success:
            raise HTTPException(404, "Watch not found or access denied")
        
        return {
            "success": True,
            "message": "Watch removed",
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to remove watch: {e}")


# ── Screenshot Endpoint ──────────────────────────────────────────────

class ScreenshotRequest(BaseModel):
    url: str
    full_page: bool = True
    format: Literal["png", "jpeg"] = "png"
    quality: Optional[int] = None
    stealth: bool = False


@app.post("/v1/screenshot")
async def capture_screenshot_endpoint(req: ScreenshotRequest, request: Request, user: dict = Depends(require_auth)):
    """
    Capture a screenshot of a webpage.
    
    Args:
        url: URL to screenshot
        full_page: Capture full page (True) or viewport only (False)
        format: Image format (png or jpeg)
        quality: JPEG quality (1-100, only for jpeg)
        stealth: Enable anti-bot stealth mode
    
    Returns:
        Screenshot data (base64 encoded)
    """
    # SSRF protection
    try:
        validate_url(req.url)
    except ValueError as e:
        raise HTTPException(400, str(e))
    
    # Rate limiting
    plan = user.get('plan', 'free')
    rate_limits_per_min = {'free': 5, 'starter': 20, 'pro': 100, 'enterprise': 1000}
    max_requests = rate_limits_per_min.get(plan, 5)
    
    client_ip = get_client_ip(request)
    if not rate_limiter.check(f"screenshot:{user.get('id', client_ip)}", max_requests, 60):
        raise HTTPException(429, "Too many screenshot requests. Try again later.")
    
    try:
        from playwright.async_api import async_playwright
        from ..core.screenshot import capture_screenshot
        from ..core.stealth import apply_stealth
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Apply stealth if requested
            if req.stealth:
                await apply_stealth(page)
            
            # Navigate to page
            await page.goto(req.url, timeout=30000, wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)
            
            # Capture screenshot
            screenshot_data = await capture_screenshot(
                page,
                full_page=req.full_page,
                format=req.format,
                quality=req.quality,
            )
            
            await browser.close()
            
            # Log usage
            if user.get("id") and user["id"] not in ["anonymous", "master"]:
                db.log_usage(
                    api_key_id=user["id"],
                    endpoint="/v1/screenshot",
                    url=req.url,
                    content_length=screenshot_data.get("size_bytes", 0),
                    success=screenshot_data.get("success", False),
                )
            
            return {
                "success": True,
                "url": req.url,
                "screenshot": screenshot_data,
            }
    
    except ImportError:
        raise HTTPException(500, "Playwright not installed")
    except Exception as e:
        raise HTTPException(500, f"Screenshot capture failed: {e}")


# ── HTML Pages ───────────────────────────────────────────────────────

from .pages import LANDING_PAGE, SIGNUP_PAGE, LOGIN_PAGE, DASHBOARD_PAGE, ADMIN_PAGE


@app.get("/", response_class=HTMLResponse)
async def landing():
    """Landing page."""
    return LANDING_PAGE


@app.get("/signup", response_class=HTMLResponse)
async def signup_page():
    """Signup page."""
    return SIGNUP_PAGE


@app.get("/login", response_class=HTMLResponse)
async def login_page():
    """Login page."""
    return LOGIN_PAGE


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page():
    """User dashboard."""
    return DASHBOARD_PAGE


@app.get("/admin", response_class=HTMLResponse)
async def admin_page():
    """Admin dashboard."""
    return ADMIN_PAGE


# Old landing HTML (keeping for reference, can remove)
OLD_LANDING_HTML = """<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CrawlKit — Web + Video Intelligence API for AI</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',system-ui,sans-serif;background:#09090b;color:#fafafa;line-height:1.6}
.container{max-width:1100px;margin:0 auto;padding:0 24px}

/* Hero */
.hero{padding:80px 0 60px;text-align:center}
.hero .badge{display:inline-block;padding:6px 16px;border-radius:999px;background:#1e1b4b;color:#818cf8;font-size:13px;font-weight:600;margin-bottom:24px;border:1px solid #312e81}
.hero h1{font-size:clamp(36px,5vw,56px);font-weight:800;letter-spacing:-0.03em;line-height:1.1;margin-bottom:16px}
.hero h1 .gradient{background:linear-gradient(135deg,#818cf8,#6366f1,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.hero p{font-size:18px;color:#a1a1aa;max-width:600px;margin:0 auto 32px}

/* Code block */
.code-block{background:#18181b;border:1px solid #27272a;border-radius:12px;padding:24px;text-align:left;max-width:700px;margin:0 auto 48px;overflow-x:auto}
.code-block pre{font-family:'JetBrains Mono',monospace;font-size:14px;color:#d4d4d8;line-height:1.8}
.code-block .comment{color:#52525b}
.code-block .string{color:#86efac}
.code-block .keyword{color:#818cf8}
.code-block .func{color:#fbbf24}

/* Features */
.features{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px;padding:40px 0}
.feature{background:#18181b;border:1px solid #27272a;border-radius:12px;padding:24px}
.feature .icon{font-size:28px;margin-bottom:12px}
.feature h3{font-size:16px;font-weight:600;margin-bottom:8px}
.feature p{font-size:14px;color:#a1a1aa}

/* Parsers */
.parsers{padding:40px 0}
.parsers h2{font-size:24px;font-weight:700;margin-bottom:24px;text-align:center}
.parser-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px}
.parser-card{background:#18181b;border:1px solid #27272a;border-radius:8px;padding:16px;text-align:center}
.parser-card .domain{color:#818cf8;font-size:13px;font-weight:600}
.parser-card .name{font-size:14px;color:#a1a1aa;margin-top:4px}

/* Pricing */
.pricing{padding:60px 0}
.pricing h2{font-size:24px;font-weight:700;margin-bottom:24px;text-align:center}
.pricing-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px}
.price-card{background:#18181b;border:1px solid #27272a;border-radius:12px;padding:24px}
.price-card.popular{border-color:#818cf8;position:relative}
.price-card.popular::before{content:'Phổ biến';position:absolute;top:-10px;left:50%;transform:translateX(-50%);background:#818cf8;color:#fff;padding:2px 12px;border-radius:999px;font-size:12px;font-weight:600}
.price-card h3{font-size:16px;font-weight:600;margin-bottom:8px}
.price-card .price{font-size:28px;font-weight:800;margin-bottom:4px}
.price-card .price span{font-size:14px;font-weight:400;color:#71717a}
.price-card .desc{font-size:13px;color:#a1a1aa;margin-bottom:16px}
.price-card ul{list-style:none;font-size:13px;color:#d4d4d8}
.price-card li{padding:4px 0}
.price-card li::before{content:'✓ ';color:#22c55e}

/* CTA */
.cta{text-align:center;padding:40px 0}
.cta a{display:inline-block;padding:14px 32px;background:#6366f1;color:#fff;border-radius:8px;font-weight:600;text-decoration:none;font-size:16px}
.cta a:hover{background:#818cf8}

/* Footer */
footer{text-align:center;padding:40px 0;color:#52525b;font-size:13px;border-top:1px solid #27272a}
</style>
</head>
<body>

<div class="container">
<div class="hero">
    <div class="badge">⚡ Web + Video Intelligence API for AI</div>
    <h1>Turn any webpage or video into<br><span class="gradient">structured data for AI</span></h1>
    <p>Crawl websites and extract video transcripts. Domain-specific parsers for legal, news, real estate, finance. RAG-ready chunks with metadata. The only crawler that does both web and video.</p>
</div>

<div class="code-block">
<pre><span class="comment"># Crawl any website → structured data</span>
<span class="keyword">import</span> httpx

resp = httpx.post(<span class="string">"https://api.crawlkit.ai/v1/scrape"</span>, json={
    <span class="string">"url"</span>: <span class="string">"https://example.com/article"</span>,
    <span class="string">"chunk"</span>: <span class="keyword">True</span>
}, headers={<span class="string">"Authorization"</span>: <span class="string">"Bearer ck_xxx"</span>})

data = resp.json()[<span class="string">"data"</span>]
<span class="func">print</span>(data[<span class="string">"title"</span>])           <span class="comment"># → "Article Title"</span>
<span class="func">print</span>(data[<span class="string">"content_type"</span>])    <span class="comment"># → "news" / "legal" / "video"</span>
<span class="func">print</span>(<span class="func">len</span>(data[<span class="string">"chunks"</span>]))     <span class="comment"># → 15 RAG-ready chunks</span>

<span class="comment"># Same API for video — auto-detects YouTube, TikTok, Facebook</span>
resp2 = httpx.post(<span class="string">"https://api.crawlkit.ai/v1/scrape"</span>, json={
    <span class="string">"url"</span>: <span class="string">"https://youtube.com/watch?v=..."</span>
})
<span class="func">print</span>(resp2.json()[<span class="string">"data"</span>][<span class="string">"structured"</span>][<span class="string">"transcript"</span>][:100])
<span class="comment"># → Full video transcript, chunked for RAG</span></pre>
</div>

<div class="features">
    <div class="feature">
        <div class="icon">⚡</div>
        <h3>Smart Rendering</h3>
        <p>Auto-detects static vs JS-heavy pages. Handles SPAs, government sites, and dynamic content without config.</p>
    </div>
    <div class="feature">
        <div class="icon">🎬</div>
        <h3>Video Crawling</h3>
        <p>Extract transcripts from YouTube, TikTok, Facebook. Full metadata + auto-captions. No video download needed.</p>
    </div>
    <div class="feature">
        <div class="icon">🏛️</div>
        <h3>Domain Parsers</h3>
        <p>Specialized parsers for legal, news, real estate, finance. Extract structured metadata per domain.</p>
    </div>
    <div class="feature">
        <div class="icon">🔍</div>
        <h3>Auto Detection</h3>
        <p>Detects content type automatically: legal, news, real estate, finance, video. Applies the right parser.</p>
    </div>
    <div class="feature">
        <div class="icon">📦</div>
        <h3>RAG-Ready Chunks</h3>
        <p>Markdown, JSON, JSONL output. Chunks with rich metadata. Import directly into any vector database.</p>
    </div>
    <div class="feature">
        <div class="icon">🚀</div>
        <h3>Batch & Discover</h3>
        <p>Crawl hundreds of URLs in one call. Discover content from sitemaps. Built for AI agent pipelines.</p>
    </div>
</div>

<div class="parsers">
    <h2>Parsers</h2>
    <div class="parser-grid">
        <div class="parser-card"><div class="domain">YouTube</div><div class="name">Video Transcripts</div></div>
        <div class="parser-card"><div class="domain">TikTok</div><div class="name">Video + Captions</div></div>
        <div class="parser-card"><div class="domain">Facebook</div><div class="name">Video + Reels</div></div>
        <div class="parser-card"><div class="domain">Legal Sites</div><div class="name">Laws & Regulations</div></div>
        <div class="parser-card"><div class="domain">News Sites</div><div class="name">Articles & Reports</div></div>
        <div class="parser-card"><div class="domain">Real Estate</div><div class="name">Property Listings</div></div>
        <div class="parser-card"><div class="domain">Finance</div><div class="name">Stock & Market Data</div></div>
        <div class="parser-card"><div class="domain">+ Any URL</div><div class="name">Generic Parser</div></div>
    </div>
</div>

<div class="pricing">
    <h2>Pricing</h2>
    <div class="pricing-grid">
        <div class="price-card">
            <h3>Free</h3>
            <div class="price">$0</div>
            <div class="desc">Get started</div>
            <ul>
                <li>20 requests/hour</li>
                <li>5 URLs/batch</li>
                <li>All parsers included</li>
                <li>Markdown + JSON output</li>
            </ul>
        </div>
        <div class="price-card popular">
            <h3>Starter</h3>
            <div class="price">$19<span>/mo</span></div>
            <div class="desc">Side projects & MVPs</div>
            <ul>
                <li>200 requests/hour</li>
                <li>50 URLs/batch</li>
                <li>Video transcripts</li>
                <li>RAG-ready chunking</li>
            </ul>
        </div>
        <div class="price-card">
            <h3>Pro</h3>
            <div class="price">$79<span>/mo</span></div>
            <div class="desc">Production apps</div>
            <ul>
                <li>2,000 requests/hour</li>
                <li>500 URLs/batch</li>
                <li>Custom parsers</li>
                <li>Webhook + priority support</li>
            </ul>
        </div>
        <div class="price-card">
            <h3>Enterprise</h3>
            <div class="price">Custom</div>
            <div class="desc">Scale unlimited</div>
            <ul>
                <li>Unlimited requests</li>
                <li>Dedicated infrastructure</li>
                <li>Custom domain parsers</li>
                <li>SLA + dedicated support</li>
            </ul>
        </div>
    </div>
</div>

<div class="cta">
    <a href="/docs">View API Documentation →</a>
</div>
</div>

<footer>
    <p>CrawlKit — Web + Video Intelligence API for AI</p>
    <p>The only crawler that turns both web pages and videos into structured data ⚡</p>
</footer>

</body>
</html>"""
