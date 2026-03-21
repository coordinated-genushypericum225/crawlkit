#!/usr/bin/env python3
"""
Test script for the new format parameter.
Tests markdown, text, and html_clean formats.
"""

import httpx
import json
import os

API_URL = os.getenv("CRAWLKIT_API_URL", "https://api.crawlkit.org")
API_KEY = os.getenv("CRAWLKIT_API_KEY", "ck_free_your_api_key_here")
TEST_URL = "https://vnexpress.net/thoi-su"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def test_format(format_type: str):
    """Test a specific format."""
    print(f"\n{'='*60}")
    print(f"Testing format: {format_type}")
    print('='*60)
    
    payload = {
        "url": TEST_URL,
        "format": format_type,
        "chunk": False
    }
    
    try:
        resp = httpx.post(
            f"{API_URL}/v1/scrape",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        print(f"Status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get("success"):
                result = data["data"]
                print(f"✓ Success!")
                print(f"  Title: {result.get('title', 'N/A')[:80]}")
                print(f"  Format: {result.get('format', 'N/A')}")
                print(f"  Content length: {result.get('content_length', 0)} chars")
                print(f"  Parser used: {result.get('parser_used', 'N/A')}")
                
                # Show a preview of content
                content = result.get("content", "")
                if content:
                    preview = content[:200].replace('\n', ' ')
                    print(f"  Preview: {preview}...")
                
                return True
            else:
                print(f"✗ Failed: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"✗ HTTP Error: {resp.status_code}")
            print(resp.text[:500])
            return False
    
    except Exception as e:
        print(f"✗ Exception: {e}")
        return False

def test_discover():
    """Test the discover endpoint."""
    print(f"\n{'='*60}")
    print(f"Testing discover endpoint")
    print('='*60)
    
    payload = {
        "url": "https://vnexpress.net/thoi-su",
        "limit": 10
    }
    
    try:
        resp = httpx.post(
            f"{API_URL}/v1/discover",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        print(f"Status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get("success"):
                count = data.get("count", 0)
                urls = data.get("urls", [])
                print(f"✓ Success!")
                print(f"  Found {count} URLs")
                
                if urls:
                    print(f"  First 3 URLs:")
                    for i, url_data in enumerate(urls[:3], 1):
                        title = url_data.get("title", "N/A")[:60]
                        print(f"    {i}. {title}")
                
                return count > 0
            else:
                print(f"✗ Failed: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"✗ HTTP Error: {resp.status_code}")
            print(resp.text[:500])
            return False
    
    except Exception as e:
        print(f"✗ Exception: {e}")
        return False

def main():
    print("CrawlKit Format Testing")
    print("="*60)
    
    results = {}
    
    # Test each format
    results["markdown"] = test_format("markdown")
    results["text"] = test_format("text")
    results["html_clean"] = test_format("html_clean")
    
    # Test discover
    results["discover"] = test_discover()
    
    # Summary
    print(f"\n{'='*60}")
    print("Summary")
    print('='*60)
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {test_name:15} {status}")
    
    all_passed = all(results.values())
    print(f"\nOverall: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())
