"""
Test the Learning Engine — self-improving extraction.

Tests:
1. First crawl — should learn pattern
2. Second crawl — should use learned pattern
3. Learning stats endpoint
4. Feedback endpoint
"""

import asyncio
import httpx
import os
from crawlkit.core.crawler import CrawlKit
from crawlkit.intelligence import PatternStorage, LearningEngine


async def test_learning_flow():
    """Test the complete learning flow: learn → apply → stats."""
    print("\n" + "=" * 60)
    print("🧠 Testing CrawlKit Learning Engine")
    print("=" * 60)
    
    # Initialize learning engine with Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL", "https://your-project.supabase.co")
    SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not SUPABASE_KEY:
        print("\n❌ SUPABASE_SERVICE_KEY not set. Set it in environment.")
        return
    
    # Initialize storage and learning engine
    print("\n1️⃣ Initializing learning engine...")
    storage = PatternStorage(supabase_url=SUPABASE_URL, supabase_key=SUPABASE_KEY)
    learning_engine = LearningEngine(storage=storage)
    
    # Initialize crawler with learning engine
    crawler = CrawlKit(learning_engine=learning_engine)
    
    # Test URL — Vietnamese news site
    test_url = "https://vnexpress.net/tham-nhung-chay-noi-cua-ong-cuu-thu-truong-bo-giao-thong-4855072.html"
    
    print(f"\n2️⃣ First crawl — learning from: {test_url}")
    result1 = await crawler.scrape(test_url, auto_extract=True)
    
    if result1.error:
        print(f"   ❌ Error: {result1.error}")
        return
    
    print(f"   ✅ Success!")
    print(f"   Parser used: {result1.parser_used}")
    print(f"   Title: {result1.title}")
    print(f"   Content length: {len(result1.markdown)} chars")
    print(f"   Content type: {result1.content_type}")
    
    # Check if pattern was learned
    print("\n3️⃣ Checking if pattern was learned...")
    domain = "vnexpress.net"
    patterns = storage.get_patterns(domain)
    
    if patterns:
        print(f"   ✅ Learned {len(patterns)} pattern(s) for {domain}")
        for p in patterns:
            print(f"      • URL pattern: {p.url_pattern}")
            print(f"      • Quality score: {p.quality_score:.2f}")
            print(f"      • Content selectors: {p.content_selectors[:2]}")
    else:
        print(f"   ⚠️ No patterns learned yet (quality may be too low)")
    
    # Second crawl — should use learned pattern
    test_url2 = "https://vnexpress.net/di-xe-may-nuoc-ngoai-ve-viet-nam-phai-lam-gi-4854925.html"
    
    print(f"\n4️⃣ Second crawl — should use learned pattern: {test_url2}")
    result2 = await crawler.scrape(test_url2, auto_extract=True)
    
    if result2.error:
        print(f"   ❌ Error: {result2.error}")
    else:
        print(f"   ✅ Success!")
        print(f"   Parser used: {result2.parser_used}")
        print(f"   Used learned pattern: {'learned:' in result2.parser_used}")
        print(f"   Title: {result2.title}")
        print(f"   Content length: {len(result2.markdown)} chars")
    
    # Get learning stats
    print("\n5️⃣ Learning engine statistics:")
    stats = storage.get_stats()
    
    print(f"   Storage: {stats.get('storage', 'unknown')}")
    print(f"   Cache size: {stats.get('cache_size', 0)} / {stats.get('cache_maxsize', 0)}")
    print(f"   Total patterns: {stats.get('total_patterns', 0)}")
    print(f"   Unique domains: {stats.get('unique_domains', 0)}")
    print(f"   Avg quality: {stats.get('avg_quality', 0):.3f}")
    
    if stats.get('top_domains'):
        print("\n   Top domains:")
        for domain in stats['top_domains'][:5]:
            print(f"      • {domain.get('domain', 'N/A')}: {domain.get('total_crawls', 0)} crawls, quality {domain.get('avg_quality_score', 0):.2f}")
    
    print("\n" + "=" * 60)
    print("✅ Learning engine test complete!")
    print("=" * 60)


async def test_api_endpoints():
    """Test learning API endpoints."""
    print("\n" + "=" * 60)
    print("🌐 Testing Learning API Endpoints")
    print("=" * 60)
    
    base_url = os.getenv("CRAWLKIT_API_URL", "http://localhost:8080")
    master_key = os.getenv("CRAWLKIT_MASTER_KEY", "ck_master_dev")
    
    headers = {"Authorization": f"Bearer {master_key}"}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test learning stats endpoint
        print("\n1️⃣ Testing GET /v1/admin/learning/stats")
        try:
            resp = await client.get(f"{base_url}/v1/admin/learning/stats", headers=headers)
            print(f"   Status: {resp.status_code}")
            
            if resp.status_code == 200:
                data = resp.json()
                print(f"   ✅ Success:")
                print(f"      {data}")
            else:
                print(f"   ❌ Error: {resp.text}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        # Test feedback endpoint
        print("\n2️⃣ Testing POST /v1/feedback")
        try:
            feedback = {
                "url": "https://vnexpress.net/test-article.html",
                "feedback": "good",
                "details": "Extraction was perfect!",
            }
            resp = await client.post(f"{base_url}/v1/feedback", json=feedback, headers=headers)
            print(f"   Status: {resp.status_code}")
            
            if resp.status_code == 200:
                data = resp.json()
                print(f"   ✅ Success: {data.get('message', 'OK')}")
            else:
                print(f"   ❌ Error: {resp.text}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    print("\n" + "=" * 60)
    print("✅ API endpoint tests complete!")
    print("=" * 60)


async def main():
    """Run all tests."""
    # Test 1: Direct learning engine
    await test_learning_flow()
    
    # Test 2: API endpoints (only if server is running)
    try:
        await test_api_endpoints()
    except Exception as e:
        print(f"\n⚠️ API endpoint tests skipped (server not running): {e}")


if __name__ == "__main__":
    asyncio.run(main())
