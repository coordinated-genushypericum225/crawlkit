#!/usr/bin/env python3
"""
Comprehensive API endpoint test suite.
Tests all endpoints against production API.
"""

import httpx
import json
import time
import os

API_URL = os.getenv("CRAWLKIT_API_URL", "https://api.crawlkit.org")
TEST_KEY = os.getenv("CRAWLKIT_API_KEY", "ck_free_your_api_key_here")
MASTER_KEY = os.getenv("CRAWLKIT_MASTER_KEY", "ck_master_your_secret_key_here")

def test_endpoint(name, method, endpoint, headers=None, json_data=None, expected_status=200):
    """Test a single endpoint."""
    print(f"\n{'='*60}")
    print(f"Testing: {method} {endpoint}")
    print(f"{'='*60}")
    
    url = f"{API_URL}{endpoint}"
    headers = headers or {}
    
    try:
        if method == "GET":
            resp = httpx.get(url, headers=headers, timeout=30)
        elif method == "POST":
            resp = httpx.post(url, headers=headers, json=json_data, timeout=30)
        elif method == "DELETE":
            resp = httpx.delete(url, headers=headers, timeout=30)
        else:
            print(f"❌ Unknown method: {method}")
            return False
        
        print(f"Status: {resp.status_code}")
        
        if resp.status_code != expected_status:
            print(f"❌ FAIL - Expected {expected_status}, got {resp.status_code}")
            print(f"Response: {resp.text[:500]}")
            return False
        
        # Try to parse JSON
        try:
            data = resp.json()
            print(f"✓ Response is valid JSON")
            
            # Print key info
            if "success" in data:
                print(f"  Success: {data['success']}")
            if "data" in data:
                d = data["data"]
                if isinstance(d, dict):
                    print(f"  Data keys: {list(d.keys())[:10]}")
                    if "title" in d:
                        print(f"  Title: {d['title'][:60]}")
                    if "content_length" in d:
                        print(f"  Content length: {d['content_length']}")
                elif isinstance(d, list):
                    print(f"  Data is list with {len(d)} items")
            if "count" in data:
                print(f"  Count: {data['count']}")
            if "urls" in data and isinstance(data["urls"], list):
                print(f"  URLs count: {len(data['urls'])}")
            
            print(f"✓ PASS")
            return True
            
        except json.JSONDecodeError:
            print(f"Response (non-JSON): {resp.text[:200]}")
            if resp.status_code == expected_status:
                print(f"✓ PASS (HTML response)")
                return True
            else:
                print(f"❌ FAIL")
                return False
    
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def main():
    print("="*60)
    print("CrawlKit API Endpoint Audit")
    print("="*60)
    
    results = {}
    
    # Public endpoints
    results["GET /v1/health"] = test_endpoint(
        "Health check",
        "GET",
        "/v1/health",
        expected_status=200
    )
    
    results["GET /v1/parsers"] = test_endpoint(
        "List parsers",
        "GET",
        "/v1/parsers",
        expected_status=200
    )
    
    results["GET /v1/settings"] = test_endpoint(
        "Public settings",
        "GET",
        "/v1/settings",
        expected_status=200
    )
    
    # Scraping endpoints
    results["POST /v1/scrape (VnExpress article)"] = test_endpoint(
        "Scrape VnExpress article",
        "POST",
        "/v1/scrape",
        headers={"Authorization": f"Bearer {TEST_KEY}"},
        json_data={
            "url": "https://vnexpress.net/tong-bi-thu-thu-tuong-du-khoi-cong-121-truong-noi-tru-bien-gioi-5052220.html",
            "format": "markdown"
        },
        expected_status=200
    )
    
    results["POST /v1/scrape (VnExpress listing)"] = test_endpoint(
        "Scrape VnExpress listing page",
        "POST",
        "/v1/scrape",
        headers={"Authorization": f"Bearer {TEST_KEY}"},
        json_data={
            "url": "https://vnexpress.net/thoi-su",
            "format": "markdown"
        },
        expected_status=200
    )
    
    results["POST /v1/scrape (YouTube)"] = test_endpoint(
        "Scrape YouTube video",
        "POST",
        "/v1/scrape",
        headers={"Authorization": f"Bearer {TEST_KEY}"},
        json_data={
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "format": "text"
        },
        expected_status=200
    )
    
    results["POST /v1/scrape (CafeF - expect 500 or 422)"] = test_endpoint(
        "Scrape CafeF (JS-heavy site)",
        "POST",
        "/v1/scrape",
        headers={"Authorization": f"Bearer {TEST_KEY}"},
        json_data={
            "url": "https://cafef.vn/",
            "format": "markdown"
        },
        expected_status=422  # Expect fetch error due to Playwright not available
    )
    
    results["POST /v1/batch"] = test_endpoint(
        "Batch scrape",
        "POST",
        "/v1/batch",
        headers={"Authorization": f"Bearer {TEST_KEY}"},
        json_data={
            "urls": [
                "https://vnexpress.net/",
                "https://vnexpress.net/thoi-su"
            ],
            "format": "text"
        },
        expected_status=200
    )
    
    results["POST /v1/discover"] = test_endpoint(
        "Discover URLs",
        "POST",
        "/v1/discover",
        headers={"Authorization": f"Bearer {TEST_KEY}"},
        json_data={
            "url": "https://vnexpress.net",
            "limit": 10
        },
        expected_status=200
    )
    
    # Auth endpoints
    results["GET /v1/auth/me"] = test_endpoint(
        "Get current user",
        "GET",
        "/v1/auth/me",
        headers={"Authorization": f"Bearer {TEST_KEY}"},
        expected_status=200
    )
    
    results["GET /v1/auth/usage"] = test_endpoint(
        "Get usage stats",
        "GET",
        "/v1/auth/usage",
        headers={"Authorization": f"Bearer {TEST_KEY}"},
        expected_status=200
    )
    
    # Admin endpoints (with master key)
    results["GET /v1/admin/users"] = test_endpoint(
        "List users (admin)",
        "GET",
        "/v1/admin/users",
        headers={"Authorization": f"Bearer {MASTER_KEY}"},
        expected_status=200
    )
    
    results["GET /v1/admin/keys"] = test_endpoint(
        "List all API keys (admin)",
        "GET",
        "/v1/admin/keys",
        headers={"Authorization": f"Bearer {MASTER_KEY}"},
        expected_status=200
    )
    
    results["GET /v1/admin/stats"] = test_endpoint(
        "Get admin stats",
        "GET",
        "/v1/admin/stats",
        headers={"Authorization": f"Bearer {MASTER_KEY}"},
        expected_status=200
    )
    
    results["GET /v1/admin/payments"] = test_endpoint(
        "List payments (admin)",
        "GET",
        "/v1/admin/payments",
        headers={"Authorization": f"Bearer {MASTER_KEY}"},
        expected_status=200
    )
    
    results["GET /v1/admin/settings"] = test_endpoint(
        "Get settings (admin)",
        "GET",
        "/v1/admin/settings",
        headers={"Authorization": f"Bearer {MASTER_KEY}"},
        expected_status=200
    )
    
    # HTML pages (expect HTML, not JSON)
    results["GET /"] = test_endpoint(
        "Landing page",
        "GET",
        "/",
        expected_status=200
    )
    
    results["GET /dashboard"] = test_endpoint(
        "Dashboard page",
        "GET",
        "/dashboard",
        expected_status=200
    )
    
    results["GET /admin"] = test_endpoint(
        "Admin page",
        "GET",
        "/admin",
        expected_status=200
    )
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{status:8} {name}")
    
    print(f"\n{passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n✓ ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n❌ {total - passed} tests failed")
        return 1


if __name__ == "__main__":
    exit(main())
