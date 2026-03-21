"""CrawlKit API client."""

import json
import os
import time
import webbrowser
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from .exceptions import (
    AuthenticationError,
    CrawlKitError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)
from .types import ParserInfo, ScrapeResult, UsageStats

CREDENTIALS_FILE = Path.home() / ".crawlkit" / "credentials.json"


class CrawlKit:
    """Synchronous CrawlKit API client."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.crawlkit.org",
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        """
        Initialize CrawlKit client.
        
        Args:
            api_key: Your CrawlKit API key (optional - will auto-load from ~/.crawlkit/credentials.json)
            base_url: API base URL (default: Railway URL, will be api.crawlkit.ai)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for rate limits
        """
        self.api_key = api_key or self._load_credentials()
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self.timeout = timeout
        
        # Only create client if we have an API key
        self._client: Optional[httpx.Client] = None
        if self.api_key:
            self._init_client()
    
    def _init_client(self):
        """Initialize HTTP client with current API key."""
        if self._client:
            self._client.close()
        
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=self.timeout,
        )
    
    def _load_credentials(self) -> Optional[str]:
        """Load saved credentials from ~/.crawlkit/credentials.json"""
        if CREDENTIALS_FILE.exists():
            try:
                with open(CREDENTIALS_FILE, 'r') as f:
                    creds = json.load(f)
                    return creds.get("api_key")
            except (json.JSONDecodeError, IOError):
                pass
        return None
    
    def _save_credentials(self, api_key: str, user_info: Optional[Dict] = None):
        """Save credentials to ~/.crawlkit/credentials.json"""
        CREDENTIALS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CREDENTIALS_FILE, 'w') as f:
            json.dump({"api_key": api_key, "user": user_info}, f, indent=2)
        # Secure file permissions - owner read/write only
        os.chmod(CREDENTIALS_FILE, 0o600)
    
    def login(self, open_browser: bool = True) -> bool:
        """
        OAuth Device Flow login — opens browser for authentication.
        
        Args:
            open_browser: Whether to automatically open the browser (default: True)
        
        Returns:
            True if login succeeded, False otherwise
        """
        # Step 1: Start device flow
        try:
            # Use a temporary client without auth for device flow endpoints
            temp_client = httpx.Client(base_url=self.base_url, timeout=self.timeout)
            
            resp = temp_client.post(
                "/v1/auth/device/start",
                json={"client_name": "CrawlKit Python SDK"}
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"❌ Failed to start device flow: {e}")
            return False
        
        device_code = data["device_code"]
        user_code = data["user_code"]
        verification_url = data["verification_url"]
        interval = data.get("interval", 5)
        expires_in = data.get("expires_in", 600)
        
        print(f"\n🔐 CrawlKit Login")
        print(f"Open this URL in your browser:\n")
        print(f"  {verification_url}\n")
        print(f"Your code: {user_code}\n")
        
        if open_browser:
            try:
                webbrowser.open(verification_url)
            except Exception:
                pass  # Browser open failed, user can open manually
        
        # Step 2: Poll for approval
        print("Waiting for authorization...", end="", flush=True)
        start = time.time()
        
        while time.time() - start < expires_in:
            time.sleep(interval)
            print(".", end="", flush=True)
            
            try:
                poll_resp = temp_client.post(
                    "/v1/auth/device/poll",
                    json={"device_code": device_code}
                )
                
                if poll_resp.status_code == 410:
                    print("\n❌ Code expired. Try again.")
                    return False
                
                if poll_resp.status_code == 429:
                    # Rate limited, wait a bit longer
                    time.sleep(2)
                    continue
                
                poll_data = poll_resp.json()
                
                if poll_data.get("status") == "approved":
                    api_key = poll_data["api_key"]
                    user_info = poll_data.get("user")
                    
                    self.api_key = api_key
                    self._init_client()
                    self._save_credentials(api_key, user_info)
                    
                    print(f"\n✅ Logged in as {user_info.get('email', 'unknown')}!")
                    print(f"Credentials saved to {CREDENTIALS_FILE}")
                    return True
                    
            except Exception as e:
                print(f"\n❌ Poll error: {e}")
                return False
        
        print("\n❌ Timed out. Try again.")
        return False
    
    def logout(self):
        """Remove saved credentials."""
        if CREDENTIALS_FILE.exists():
            CREDENTIALS_FILE.unlink()
            self.api_key = None
            if self._client:
                self._client.close()
                self._client = None
            print("✅ Logged out. Credentials removed.")
        else:
            print("ℹ️  No saved credentials found.")
    
    def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Make HTTP request with error handling and retries."""
        if not self._client:
            raise AuthenticationError(
                "No API key configured. Run `crawlkit login` or pass api_key to CrawlKit()"
            )
        
        url = endpoint
        retries = 0
        
        while retries <= self.max_retries:
            try:
                response = self._client.request(method, url, **kwargs)
                
                # Handle different status codes
                if response.status_code == 401:
                    raise AuthenticationError("Invalid API key")
                elif response.status_code == 404:
                    raise NotFoundError(f"Resource not found: {url}")
                elif response.status_code == 422:
                    raise ValidationError(response.json().get("detail", "Validation error"))
                elif response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    if retries < self.max_retries:
                        time.sleep(min(retry_after, 2 ** retries))
                        retries += 1
                        continue
                    raise RateLimitError("Rate limit exceeded", retry_after=retry_after)
                elif response.status_code >= 500:
                    if retries < self.max_retries:
                        time.sleep(2 ** retries)
                        retries += 1
                        continue
                    raise ServerError(f"Server error: {response.status_code}")
                
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPError as e:
                if retries < self.max_retries and isinstance(e, httpx.TimeoutException):
                    retries += 1
                    time.sleep(2 ** retries)
                    continue
                raise CrawlKitError(f"HTTP error: {str(e)}") from e
        
        raise CrawlKitError("Max retries exceeded")
    
    def scrape(
        self,
        url: str,
        chunk: bool = False,
        chunk_size: int = 1000,
        parser: Optional[str] = None,
    ) -> ScrapeResult:
        """
        Scrape a URL and return structured content.
        
        Args:
            url: URL to scrape
            chunk: Whether to split content into chunks
            chunk_size: Size of each chunk (if chunking enabled)
            parser: Specific parser to use (optional)
        
        Returns:
            ScrapeResult with content, title, and metadata
        """
        params = {"url": url}
        if chunk:
            params["chunk"] = "true"
            params["chunk_size"] = chunk_size
        if parser:
            params["parser"] = parser
        
        data = self._request("GET", "/scrape", params=params)
        return ScrapeResult.from_dict(data)
    
    def batch(
        self,
        urls: List[str],
        chunk: bool = False,
        chunk_size: int = 1000,
    ) -> List[ScrapeResult]:
        """
        Scrape multiple URLs in one request.
        
        Args:
            urls: List of URLs to scrape
            chunk: Whether to split content into chunks
            chunk_size: Size of each chunk
        
        Returns:
            List of ScrapeResults
        """
        payload = {"urls": urls}
        if chunk:
            payload["chunk"] = True
            payload["chunk_size"] = chunk_size
        
        data = self._request("POST", "/batch", json=payload)
        return [ScrapeResult.from_dict(item) for item in data.get("results", [])]
    
    def discover(self, url: str, limit: int = 20) -> List[str]:
        """
        Discover links from a page.
        
        Args:
            url: URL to discover links from
            limit: Maximum number of links to return
        
        Returns:
            List of discovered URLs
        """
        params = {"url": url, "limit": limit}
        data = self._request("GET", "/discover", params=params)
        return data.get("links", [])
    
    def health(self) -> Dict[str, Any]:
        """
        Check API health status.
        
        Returns:
            Health status information
        """
        return self._request("GET", "/health")
    
    def parsers(self) -> List[ParserInfo]:
        """
        List available parsers.
        
        Returns:
            List of available parsers
        """
        data = self._request("GET", "/parsers")
        return [ParserInfo.from_dict(p) for p in data.get("parsers", [])]
    
    def usage(self) -> UsageStats:
        """
        Get your API usage statistics.
        
        Returns:
            Usage statistics
        """
        data = self._request("GET", "/usage")
        return UsageStats.from_dict(data)
    
    def close(self):
        """Close the HTTP client."""
        self._client.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, *args):
        """Context manager exit."""
        self.close()


class AsyncCrawlKit:
    """Asynchronous CrawlKit API client."""
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.crawlkit.org",
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        """
        Initialize async CrawlKit client.
        
        Args:
            api_key: Your CrawlKit API key
            base_url: API base URL
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for rate limits
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout,
        )
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Make async HTTP request with error handling and retries."""
        url = endpoint
        retries = 0
        
        while retries <= self.max_retries:
            try:
                response = await self._client.request(method, url, **kwargs)
                
                if response.status_code == 401:
                    raise AuthenticationError("Invalid API key")
                elif response.status_code == 404:
                    raise NotFoundError(f"Resource not found: {url}")
                elif response.status_code == 422:
                    raise ValidationError(response.json().get("detail", "Validation error"))
                elif response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    if retries < self.max_retries:
                        await asyncio.sleep(min(retry_after, 2 ** retries))
                        retries += 1
                        continue
                    raise RateLimitError("Rate limit exceeded", retry_after=retry_after)
                elif response.status_code >= 500:
                    if retries < self.max_retries:
                        await asyncio.sleep(2 ** retries)
                        retries += 1
                        continue
                    raise ServerError(f"Server error: {response.status_code}")
                
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPError as e:
                if retries < self.max_retries and isinstance(e, httpx.TimeoutException):
                    retries += 1
                    await asyncio.sleep(2 ** retries)
                    continue
                raise CrawlKitError(f"HTTP error: {str(e)}") from e
        
        raise CrawlKitError("Max retries exceeded")
    
    async def scrape(
        self,
        url: str,
        chunk: bool = False,
        chunk_size: int = 1000,
        parser: Optional[str] = None,
    ) -> ScrapeResult:
        """Async scrape a URL."""
        params = {"url": url}
        if chunk:
            params["chunk"] = "true"
            params["chunk_size"] = chunk_size
        if parser:
            params["parser"] = parser
        
        data = await self._request("GET", "/scrape", params=params)
        return ScrapeResult.from_dict(data)
    
    async def batch(
        self,
        urls: List[str],
        chunk: bool = False,
        chunk_size: int = 1000,
    ) -> List[ScrapeResult]:
        """Async batch scrape."""
        payload = {"urls": urls}
        if chunk:
            payload["chunk"] = True
            payload["chunk_size"] = chunk_size
        
        data = await self._request("POST", "/batch", json=payload)
        return [ScrapeResult.from_dict(item) for item in data.get("results", [])]
    
    async def discover(self, url: str, limit: int = 20) -> List[str]:
        """Async discover links."""
        params = {"url": url, "limit": limit}
        data = await self._request("GET", "/discover", params=params)
        return data.get("links", [])
    
    async def health(self) -> Dict[str, Any]:
        """Async health check."""
        return await self._request("GET", "/health")
    
    async def parsers(self) -> List[ParserInfo]:
        """Async list parsers."""
        data = await self._request("GET", "/parsers")
        return [ParserInfo.from_dict(p) for p in data.get("parsers", [])]
    
    async def usage(self) -> UsageStats:
        """Async get usage stats."""
        data = await self._request("GET", "/usage")
        return UsageStats.from_dict(data)
    
    async def close(self):
        """Close the async HTTP client."""
        await self._client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, *args):
        """Async context manager exit."""
        await self.close()


# Import asyncio for async client
import asyncio
