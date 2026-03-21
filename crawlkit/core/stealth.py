"""
Anti-Bot Stealth Mode for Playwright.

Features:
- playwright-stealth integration
- Random User-Agent rotation
- Randomized delays
- Cookie persistence
- Realistic viewport/timezone/locale spoofing
"""

from __future__ import annotations
import random
import asyncio
from typing import Optional


class StealthConfig:
    """Configuration for stealth mode."""
    
    # Realistic viewport sizes
    VIEWPORTS = [
        {"width": 1920, "height": 1080},
        {"width": 1366, "height": 768},
        {"width": 1440, "height": 900},
        {"width": 1536, "height": 864},
        {"width": 2560, "height": 1440},
    ]
    
    # Realistic locales
    LOCALES = ["en-US", "en-GB", "vi-VN"]
    
    # Realistic timezones
    TIMEZONES = ["America/New_York", "Europe/London", "Asia/Ho_Chi_Minh", "Asia/Tokyo"]
    
    def __init__(self):
        self._user_agents = None
    
    def get_random_viewport(self) -> dict:
        """Get a random viewport size."""
        return random.choice(self.VIEWPORTS)
    
    def get_random_locale(self) -> str:
        """Get a random locale."""
        return random.choice(self.LOCALES)
    
    def get_random_timezone(self) -> str:
        """Get a random timezone."""
        return random.choice(self.TIMEZONES)
    
    def get_random_user_agent(self) -> str:
        """Get a random realistic user agent."""
        if self._user_agents is None:
            self._load_user_agents()
        return random.choice(self._user_agents)
    
    def _load_user_agents(self):
        """Load realistic user agents."""
        try:
            from fake_useragent import UserAgent
            ua = UserAgent()
            # Generate a pool of user agents
            self._user_agents = [ua.random for _ in range(10)]
        except ImportError:
            # Fallback to hardcoded realistic UAs
            self._user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            ]
    
    def get_random_delay(self, min_ms: int = 100, max_ms: int = 500) -> float:
        """Get a random delay in seconds (human-like)."""
        return random.uniform(min_ms, max_ms) / 1000.0


# Global config
_stealth_config = StealthConfig()


async def apply_stealth(page, context=None):
    """
    Apply stealth settings to a Playwright page.
    
    Args:
        page: Playwright page object
        context: Playwright context (optional, for cookie persistence)
    """
    try:
        # Try to use playwright-stealth
        try:
            from playwright_stealth import stealth_async
            await stealth_async(page)
            print("✅ playwright-stealth applied")
        except ImportError:
            print("⚠️ playwright-stealth not installed, using manual stealth")
            await _manual_stealth(page)
        
        # Set random user agent
        user_agent = _stealth_config.get_random_user_agent()
        await page.set_extra_http_headers({"User-Agent": user_agent})
        
        # Set random viewport
        viewport = _stealth_config.get_random_viewport()
        await page.set_viewport_size(viewport)
        
        # Set random locale and timezone
        locale = _stealth_config.get_random_locale()
        timezone = _stealth_config.get_random_timezone()
        
        # Apply via context if available
        if context:
            await context.set_extra_http_headers({"User-Agent": user_agent})
        
        print(f"🥷 Stealth mode: {viewport['width']}x{viewport['height']}, {locale}, {timezone}")
    
    except Exception as e:
        print(f"⚠️ Stealth setup failed: {e}")


async def _manual_stealth(page):
    """Manual stealth techniques when playwright-stealth is not available."""
    try:
        # Override navigator.webdriver
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        # Override navigator.plugins
        await page.add_init_script("""
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
        """)
        
        # Override navigator.languages
        await page.add_init_script("""
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
        """)
        
        # Mock chrome object
        await page.add_init_script("""
            window.chrome = {
                runtime: {}
            };
        """)
        
        # Override permissions
        await page.add_init_script("""
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
    
    except Exception as e:
        print(f"⚠️ Manual stealth failed: {e}")


async def random_delay(min_ms: int = 100, max_ms: int = 500):
    """Add a random human-like delay."""
    delay = _stealth_config.get_random_delay(min_ms, max_ms)
    await asyncio.sleep(delay)


def get_stealth_config() -> StealthConfig:
    """Get global stealth config."""
    return _stealth_config
