"""
HTTP fetcher with smart JS rendering detection.
Uses httpx for static pages, Playwright for JS-heavy pages.
"""

from __future__ import annotations
import time
import logging
import httpx
from bs4 import BeautifulSoup
from typing import Optional

logger = logging.getLogger(__name__)


# Sites known to require JS rendering
JS_REQUIRED_DOMAINS = {
    "thuvienphapluat.vn",
    "batdongsan.com.vn",
    "cafef.vn",
    "vietstock.vn",
    "shopee.vn",
    "tiki.vn",
    "lazada.vn",
    "dichvucong.gov.vn",
    "homedy.com",
    "nhadat.cafef.vn",
}

# Sites that work fine with static fetch
STATIC_OK_DOMAINS = {
    "vnexpress.net",
    "tuoitre.vn",
    "thanhnien.vn",
    "baochinhphu.vn",
    "congbao.chinhphu.vn",
}

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate",
}


class FetchResult:
    """Raw fetch result before parsing."""
    
    def __init__(
        self,
        url: str,
        final_url: str,
        status_code: int,
        html: str,
        headers: dict,
        rendered_js: bool = False,
        fetch_time_ms: int = 0,
    ):
        self.url = url
        self.final_url = final_url
        self.status_code = status_code
        self.html = html
        self.headers = headers
        self.rendered_js = rendered_js
        self.fetch_time_ms = fetch_time_ms


def _needs_js(url: str, html: str = "") -> bool:
    """Determine if a URL needs JS rendering."""
    from urllib.parse import urlparse
    domain = urlparse(url).netloc.lower().replace("www.", "")
    
    if domain in JS_REQUIRED_DOMAINS:
        return True
    if domain in STATIC_OK_DOMAINS:
        return False
    
    # Heuristic: check if static HTML has minimal content
    if html:
        soup = BeautifulSoup(html, "lxml")
        text = soup.get_text(strip=True)
        # If body text is very short, probably needs JS
        if len(text) < 500:
            return True
        # Check for common SPA indicators
        if any(x in html[:5000] for x in ["__NEXT_DATA__", "react-root", "vue-app", "__nuxt"]):
            return True
    
    return False


def fetch_static(
    url: str,
    headers: Optional[dict] = None,
    timeout: int = 15,
    follow_redirects: bool = True,
) -> FetchResult:
    """Fetch URL using httpx (no JS rendering)."""
    start = time.time()
    h = {**DEFAULT_HEADERS, **(headers or {})}
    
    try:
        with httpx.Client(
            headers=h,
            follow_redirects=follow_redirects,
            timeout=timeout,
        ) as client:
            resp = client.get(url)
            elapsed = int((time.time() - start) * 1000)
            
            return FetchResult(
                url=url,
                final_url=str(resp.url),
                status_code=resp.status_code,
                html=resp.text,
                headers=dict(resp.headers),
                rendered_js=False,
                fetch_time_ms=elapsed,
            )
    except Exception as e:
        elapsed = int((time.time() - start) * 1000)
        return FetchResult(
            url=url,
            final_url=url,
            status_code=0,
            html="",
            headers={},
            fetch_time_ms=elapsed,
        )


async def fetch_js(
    url: str,
    wait_ms: int = 4000,
    timeout: int = 25000,
    wait_until: str = "domcontentloaded",
) -> FetchResult:
    """Fetch URL using Playwright (with JS rendering)."""
    start = time.time()
    
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        elapsed = int((time.time() - start) * 1000)
        logger.error("Playwright not installed. Install with: pip install playwright && playwright install chromium")
        return FetchResult(
            url=url,
            final_url=url,
            status_code=500,
            html="<error>Playwright not available. JS rendering is disabled. Install Playwright to scrape JS-heavy sites.</error>",
            headers={"error": "playwright_not_installed"},
            rendered_js=False,
            fetch_time_ms=elapsed,
        )
    
    browser = None
    try:
        async with async_playwright() as p:
            try:
                browser = await p.chromium.launch(headless=True)
            except Exception as launch_error:
                elapsed = int((time.time() - start) * 1000)
                logger.error(f"Failed to launch Chromium: {launch_error}")
                return FetchResult(
                    url=url,
                    final_url=url,
                    status_code=500,
                    html=f"<error>Chromium browser unavailable: {str(launch_error)}. This site requires JS rendering but Chromium cannot start (memory/installation issue).</error>",
                    headers={"error": "chromium_launch_failed"},
                    rendered_js=False,
                    fetch_time_ms=elapsed,
                )
            
            try:
                page = await browser.new_page(
                    user_agent=DEFAULT_HEADERS["User-Agent"],
                    locale="vi-VN",
                )
                
                resp = await page.goto(url, timeout=timeout, wait_until=wait_until)
                await page.wait_for_timeout(wait_ms)
                
                html = await page.content()
                final_url = page.url
                status = resp.status if resp else 0
                
                elapsed = int((time.time() - start) * 1000)
                
                return FetchResult(
                    url=url,
                    final_url=final_url,
                    status_code=status,
                    html=html,
                    headers={},
                    rendered_js=True,
                    fetch_time_ms=elapsed,
                )
            finally:
                # Always close browser, even on error
                if browser:
                    try:
                        await browser.close()
                    except Exception as close_error:
                        logger.warning(f"Failed to close browser: {close_error}")
    except Exception as e:
        elapsed = int((time.time() - start) * 1000)
        logger.error(f"Playwright fetch failed: {e}")
        return FetchResult(
            url=url,
            final_url=url,
            status_code=500,
            html=f"<error>JS rendering failed: {str(e)}</error>",
            headers={"error": str(e)},
            rendered_js=False,
            fetch_time_ms=elapsed,
        )


async def fetch(
    url: str,
    force_js: bool = False,
    force_static: bool = False,
    js_wait_ms: int = 4000,
    headers: Optional[dict] = None,
) -> FetchResult:
    """
    Smart fetch: tries static first, falls back to JS if needed.
    
    Args:
        url: URL to fetch
        force_js: Always use Playwright
        force_static: Never use Playwright
        js_wait_ms: Wait time after JS load
        headers: Custom HTTP headers
    """
    if force_js:
        return await fetch_js(url, wait_ms=js_wait_ms)
    
    if force_static:
        return fetch_static(url, headers=headers)
    
    # Smart detection: check domain first
    if _needs_js(url):
        return await fetch_js(url, wait_ms=js_wait_ms)
    
    # Try static first
    result = fetch_static(url, headers=headers)
    
    # If content is too short, retry with JS
    if result.status_code == 200 and _needs_js(url, result.html):
        return await fetch_js(url, wait_ms=js_wait_ms)
    
    return result
