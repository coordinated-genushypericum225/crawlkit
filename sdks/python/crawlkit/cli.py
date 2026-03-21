"""CrawlKit CLI - Command-line interface for CrawlKit API."""

import sys
from typing import Optional

from .client import CrawlKit
from .exceptions import CrawlKitError


def print_usage():
    """Print CLI usage information."""
    print("""
CrawlKit CLI

Usage:
  crawlkit <command> [args]

Commands:
  login                  Login via browser (OAuth Device Flow)
  logout                 Remove saved credentials
  whoami                 Show current user info
  scrape <url>           Scrape a URL and print content
  
Examples:
  crawlkit login
  crawlkit scrape https://example.com
  crawlkit whoami
""")


def cmd_login():
    """Handle login command."""
    ck = CrawlKit()
    success = ck.login()
    sys.exit(0 if success else 1)


def cmd_logout():
    """Handle logout command."""
    ck = CrawlKit()
    ck.logout()
    sys.exit(0)


def cmd_whoami():
    """Handle whoami command."""
    ck = CrawlKit()
    
    if not ck.api_key:
        print("❌ Not logged in. Run: crawlkit login")
        sys.exit(1)
    
    try:
        # Make a request to /v1/auth/me to get user info
        user_info = ck._request("GET", "/v1/auth/me")
        user = user_info.get("user", {})
        api_key_info = user_info.get("api_key", {})
        
        print(f"\n✅ Logged in as: {user.get('email', 'unknown')}")
        print(f"Name: {user.get('name', 'N/A')}")
        print(f"Plan: {api_key_info.get('plan', user.get('plan', 'N/A'))}")
        print(f"Rate limit: {api_key_info.get('rate_limit_per_hour', 'N/A')} requests/hour")
        print(f"Max batch size: {api_key_info.get('max_batch_size', 'N/A')}")
        print()
        
    except CrawlKitError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def cmd_scrape(url: Optional[str] = None):
    """Handle scrape command."""
    if not url:
        print("❌ Error: URL required")
        print("Usage: crawlkit scrape <url>")
        sys.exit(1)
    
    ck = CrawlKit()
    
    if not ck.api_key:
        print("❌ Not logged in. Run: crawlkit login")
        sys.exit(1)
    
    try:
        print(f"🕷️  Scraping {url}...")
        result = ck.scrape(url)
        
        print("\n" + "="*60)
        print(f"Title: {result.title or 'N/A'}")
        print(f"URL: {result.url}")
        print("="*60 + "\n")
        print(result.content)
        print("\n" + "="*60)
        
    except CrawlKitError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(0)
    
    command = sys.argv[1]
    
    if command == "login":
        cmd_login()
    elif command == "logout":
        cmd_logout()
    elif command == "whoami":
        cmd_whoami()
    elif command == "scrape":
        url = sys.argv[2] if len(sys.argv) > 2 else None
        cmd_scrape(url)
    elif command in ["help", "--help", "-h"]:
        print_usage()
        sys.exit(0)
    else:
        print(f"❌ Unknown command: {command}")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
