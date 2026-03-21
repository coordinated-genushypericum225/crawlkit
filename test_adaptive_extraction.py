#!/usr/bin/env python3
"""
Test the Adaptive Content Extraction Engine on diverse URLs.
"""

import asyncio
import sys
from crawlkit.core.crawler import CrawlKit


TEST_URLS = [
    # Vietnamese article
    "https://vnexpress.net/tong-bi-thu-thu-tuong-du-khoi-cong-121-truong-noi-tru-bien-gioi-5052220.html",
    
    # Wikipedia article
    "https://en.wikipedia.org/wiki/Vietnam",
    
    # Stack Overflow question (forum)
    "https://stackoverflow.com/questions/1",
]


async def test_url(crawler, url):
    """Test adaptive extraction on a single URL."""
    print(f"\n{'='*80}")
    print(f"Testing: {url}")
    print(f"{'='*80}\n")
    
    try:
        result = await crawler.scrape(
            url=url,
            auto_extract=True,  # Use adaptive extraction
            chunk=False,
        )
        
        if result.error:
            print(f"❌ Error: {result.error}")
            return False
        
        print(f"✓ Success!")
        print(f"  Parser used: {result.parser_used}")
        print(f"  Content type: {result.content_type}")
        print(f"  Title: {result.title[:100]}")
        
        if result.metadata:
            print(f"  Metadata keys: {list(result.metadata.keys())}")
            
            # Show confidence if available
            if "extraction_confidence" in result.metadata:
                conf = result.metadata["extraction_confidence"]
                print(f"  Confidence: {conf:.2%}")
        
        if result.structured:
            print(f"  Structured keys: {list(result.structured.keys())}")
            
            # Show content-specific fields
            if result.structured.get("page_type") == "article":
                print(f"\n  Article fields:")
                if result.structured.get("author"):
                    print(f"    - Author: {result.structured['author']}")
                if result.structured.get("published_date"):
                    print(f"    - Published: {result.structured['published_date']}")
                if result.structured.get("word_count"):
                    print(f"    - Words: {result.structured['word_count']}")
            
            elif result.structured.get("page_type") == "product":
                print(f"\n  Product fields:")
                if result.structured.get("price"):
                    print(f"    - Price: {result.structured['price']} {result.structured.get('currency', '')}")
                if result.structured.get("brand"):
                    print(f"    - Brand: {result.structured['brand']}")
            
            elif result.structured.get("page_type") == "listing":
                print(f"\n  Listing fields:")
                print(f"    - Items: {result.structured.get('total_items', 0)}")
                if result.structured.get("items"):
                    print(f"    - First item: {result.structured['items'][0].get('title', '')[:80]}")
        
        # Show content preview
        if result.text or result.markdown:
            content = result.text or result.markdown
            preview = content[:500].strip()
            print(f"\n  Content preview ({len(content)} chars):")
            print(f"  {preview[:200]}...")
        
        print(f"\n  Crawl time: {result.crawl_time_ms}ms")
        
        return True
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Test adaptive extraction on all URLs."""
    print("CrawlKit Adaptive Content Extraction Test")
    print("==========================================\n")
    
    crawler = CrawlKit()
    
    results = []
    for url in TEST_URLS:
        success = await test_url(crawler, url)
        results.append((url, success))
    
    # Summary
    print(f"\n\n{'='*80}")
    print("Test Summary")
    print(f"{'='*80}\n")
    
    successes = sum(1 for _, success in results if success)
    total = len(results)
    
    for url, success in results:
        status = "✓" if success else "❌"
        print(f"{status} {url[:60]}")
    
    print(f"\nPassed: {successes}/{total}")
    
    sys.exit(0 if successes == total else 1)


if __name__ == "__main__":
    asyncio.run(main())
