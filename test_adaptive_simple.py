#!/usr/bin/env python3
"""
Simple test of adaptive extraction on a URL without a site-specific parser.
"""

import asyncio
from crawlkit.core.crawler import CrawlKit


async def main():
    """Test adaptive extraction."""
    crawler = CrawlKit()
    
    # Test on a site without a specific parser
    # Use a simple static site
    url = "https://example.com"
    
    print(f"Testing adaptive extraction on: {url}")
    print("=" * 80)
    
    result = await crawler.scrape(
        url=url,
        auto_extract=True,
        chunk=False,
    )
    
    if result.error:
        print(f"❌ Error: {result.error}")
        return
    
    print(f"✓ Success!")
    print(f"\nParser used: {result.parser_used}")
    print(f"Content type: {result.content_type}")
    print(f"Title: {result.title}")
    
    if result.metadata:
        print(f"\nMetadata:")
        for key, value in result.metadata.items():
            if isinstance(value, (str, int, float)):
                print(f"  {key}: {value}")
    
    if result.structured:
        print(f"\nStructured data:")
        for key, value in result.structured.items():
            if isinstance(value, (str, int, float)):
                print(f"  {key}: {value}")
    
    if result.text or result.markdown:
        content = result.text or result.markdown
        print(f"\nContent ({len(content)} chars):")
        print(content[:500])


if __name__ == "__main__":
    asyncio.run(main())
