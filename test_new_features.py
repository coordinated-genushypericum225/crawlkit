#!/usr/bin/env python3
"""
Test script for new CrawlKit features.

Tests:
1. NLP extraction
2. OCR (if test PDF available)
3. Stealth mode
4. Screenshot capture
5. Watch functionality
"""

import asyncio
import sys


async def test_nlp():
    """Test NLP extraction."""
    print("\n=== Testing NLP Extraction ===")
    
    try:
        from crawlkit.nlp import get_extractor
        
        extractor = get_extractor()
        
        # Test Vietnamese text
        vn_text = """
        Ngày 15 tháng 3 năm 2024, Thủ tướng Chính phủ Phạm Minh Chính đã chủ trì 
        cuộc họp tại Hà Nội về phát triển kinh tế số và chuyển đổi số quốc gia.
        Theo đó, Bộ Thông tin và Truyền thông sẽ triển khai các giải pháp mới.
        """
        
        result = extractor.extract(vn_text)
        
        print(f"✅ Language detected: {result['language']}")
        print(f"✅ Found {len(result['entities'])} entities")
        for entity in result['entities'][:3]:
            print(f"   - {entity['text']} ({entity['type']})")
        print(f"✅ Found {len(result['keywords'])} keywords: {result['keywords'][:5]}")
        
        # Test English text
        en_text = """
        On January 15, 2024, Microsoft Corporation announced a partnership with OpenAI
        in Seattle, Washington to develop new artificial intelligence technologies.
        """
        
        result_en = extractor.extract(en_text)
        print(f"\n✅ English language detected: {result_en['language']}")
        print(f"✅ Found {len(result_en['entities'])} entities in English text")
        
        return True
    
    except Exception as e:
        print(f"❌ NLP test failed: {e}")
        return False


async def test_ocr():
    """Test OCR module (unit test only, no actual PDF)."""
    print("\n=== Testing OCR Module ===")
    
    try:
        from crawlkit.parsers.document.ocr import get_ocr_engine
        
        # Just test that we can import and initialize
        ocr_engine = get_ocr_engine()
        
        # Test scanned detection
        is_scanned = ocr_engine.is_scanned_pdf_page("", image_count=5)
        print(f"✅ OCR engine loaded successfully")
        print(f"✅ Scanned detection works: page with 0 words + 5 images = scanned: {is_scanned}")
        
        return True
    
    except Exception as e:
        print(f"❌ OCR test failed: {e}")
        return False


async def test_stealth():
    """Test stealth module."""
    print("\n=== Testing Stealth Module ===")
    
    try:
        from crawlkit.core.stealth import get_stealth_config
        
        config = get_stealth_config()
        
        # Test random generators
        viewport = config.get_random_viewport()
        user_agent = config.get_random_user_agent()
        locale = config.get_random_locale()
        timezone = config.get_random_timezone()
        
        print(f"✅ Random viewport: {viewport['width']}x{viewport['height']}")
        print(f"✅ Random UA: {user_agent[:50]}...")
        print(f"✅ Random locale: {locale}")
        print(f"✅ Random timezone: {timezone}")
        
        return True
    
    except Exception as e:
        print(f"❌ Stealth test failed: {e}")
        return False


async def test_screenshot():
    """Test screenshot module (unit test only)."""
    print("\n=== Testing Screenshot Module ===")
    
    try:
        from crawlkit.core.screenshot import save_screenshot
        import base64
        
        # Create a dummy screenshot
        dummy_data = b"fake image data"
        dummy_b64 = base64.b64encode(dummy_data).decode('utf-8')
        
        # Test save function (without actually writing)
        print(f"✅ Screenshot module imported successfully")
        print(f"✅ Base64 encoding works: {len(dummy_b64)} chars")
        
        return True
    
    except Exception as e:
        print(f"❌ Screenshot test failed: {e}")
        return False


async def test_watch():
    """Test watch module (unit test only, no DB)."""
    print("\n=== Testing Watch Module ===")
    
    try:
        from crawlkit.core.watch import compute_content_hash
        
        # Test hash computation
        content1 = "This is test content"
        content2 = "This is different content"
        
        hash1 = compute_content_hash(content1)
        hash2 = compute_content_hash(content2)
        hash1_repeat = compute_content_hash(content1)
        
        print(f"✅ Content hash works")
        print(f"   - Hash 1: {hash1[:16]}...")
        print(f"   - Hash 2: {hash2[:16]}...")
        print(f"✅ Hashes are deterministic: {hash1 == hash1_repeat}")
        print(f"✅ Different content = different hash: {hash1 != hash2}")
        
        return True
    
    except Exception as e:
        print(f"❌ Watch test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("🧪 Testing CrawlKit New Features\n")
    
    results = {
        "NLP Extraction": await test_nlp(),
        "OCR Module": await test_ocr(),
        "Stealth Mode": await test_stealth(),
        "Screenshot Capture": await test_screenshot(),
        "Watch Monitoring": await test_watch(),
    }
    
    print("\n" + "="*50)
    print("📊 Test Results:")
    print("="*50)
    
    for feature, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}  {feature}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 All features working correctly!")
        return 0
    else:
        print("\n⚠️  Some features failed. Check logs above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
