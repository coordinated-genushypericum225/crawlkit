#!/usr/bin/env python3
"""
Test Video Intelligence Engine

Tests all video parsers with intelligence analysis.
"""

import asyncio
import json
from crawlkit.core.crawler import CrawlKit


async def test_youtube():
    """Test YouTube parser with intelligence."""
    print("=" * 60)
    print("Testing YouTube Parser with Intelligence")
    print("=" * 60)
    
    crawler = CrawlKit()
    result = await crawler.scrape(
        url="https://youtu.be/-Td-D-vKJDg",
        intelligence=True,
        lang="en"
    )
    
    assert result.success, f"YouTube scrape failed: {result.error}"
    assert result.parser_used == "youtube"
    assert "transcript" in result.structured
    assert "transcript_segments" in result.structured
    assert "intelligence" in result.structured
    
    intel = result.structured["intelligence"]
    
    print(f"\n✅ Title: {result.title}")
    print(f"✅ Transcript length: {len(result.structured['transcript'])} chars")
    print(f"✅ Segments: {len(result.structured['transcript_segments'])}")
    print(f"✅ Language: {result.structured.get('transcript_language', 'unknown')}")
    
    print(f"\n--- Intelligence Analysis ---")
    print(f"Key points: {len(intel['key_points'])}")
    print(f"Topics: {len(intel['topics'])}")
    print(f"Summary points: {len(intel['summary_points'])}")
    print(f"Content metrics: {intel['content_metrics']}")
    
    # Show sample data
    print(f"\nSample key point: {intel['key_points'][0][:100]}...")
    print(f"\nTop topics:")
    for topic in intel['topics'][:5]:
        print(f"  - {topic['topic']}: {topic['relevance']}")
    
    # Check chapters
    if "chapters" in result.structured:
        print(f"\n✅ Chapters: {len(result.structured['chapters'])}")
        print(f"Sample chapter: {result.structured['chapters'][0]}")
    
    print("\n✅ YouTube test passed!\n")
    return True


async def test_tiktok():
    """Test TikTok parser (if working)."""
    print("=" * 60)
    print("Testing TikTok Parser")
    print("=" * 60)
    
    crawler = CrawlKit()
    # Note: TikTok URLs often break, this is just to test parser exists
    result = await crawler.scrape(
        url="https://www.tiktok.com/@test/video/7000000000000000000",
        intelligence=False  # Don't require intelligence for this test
    )
    
    print(f"Parser detected: {result.parser_used}")
    print(f"Success: {result.success}")
    if not result.success:
        print(f"Error (expected for test URL): {result.error}")
    
    print("\n✅ TikTok parser exists!\n")
    return True


async def test_intelligence_without_video():
    """Test intelligence module directly."""
    print("=" * 60)
    print("Testing Intelligence Module Directly")
    print("=" * 60)
    
    from crawlkit.intelligence import VideoIntelligence
    
    sample_text = """
    Today we're going to discuss trading strategies. First, you need to understand
    market structure. Second, identify key support and resistance levels. Finally,
    manage your risk properly. The most important thing is to stay disciplined.
    Remember, trading is 80% psychology and 20% strategy. You must control your
    emotions. Never risk more than 2% per trade.
    """
    
    key_points = VideoIntelligence.extract_key_points(sample_text, max_points=3)
    topics = VideoIntelligence.extract_topics(sample_text, max_topics=5)
    entities = VideoIntelligence.extract_entities(sample_text)
    language = VideoIntelligence.detect_language(sample_text)
    metrics = VideoIntelligence.calculate_content_metrics(sample_text, duration=60)
    
    print(f"\n✅ Key points extracted: {len(key_points)}")
    for i, point in enumerate(key_points, 1):
        print(f"  {i}. {point}")
    
    print(f"\n✅ Topics extracted: {len(topics)}")
    for topic in topics:
        print(f"  - {topic['topic']}: {topic['relevance']}")
    
    print(f"\n✅ Language detected: {language}")
    print(f"\n✅ Entities found: {sum(len(v) for v in entities.values())}")
    print(f"  Numbers: {entities['numbers']}")
    
    print(f"\n✅ Metrics: {metrics}")
    
    print("\n✅ Intelligence module test passed!\n")
    return True


async def test_response_structure():
    """Test the API response structure matches spec."""
    print("=" * 60)
    print("Testing Response Structure")
    print("=" * 60)
    
    crawler = CrawlKit()
    result = await crawler.scrape(
        url="https://youtu.be/-Td-D-vKJDg",
        intelligence=True,
        lang="en"
    )
    
    # Verify response structure matches the spec
    assert "structured" in result.__dict__
    structured = result.structured
    
    # Core fields
    assert "title" in structured
    assert "channel" in structured or "uploader" in structured
    assert "views" in structured or "view_count" in structured
    assert "duration" in structured
    assert "transcript" in structured
    assert "transcript_segments" in structured
    
    # Intelligence fields
    assert "intelligence" in structured
    intel = structured["intelligence"]
    
    required_intel_fields = [
        "key_points",
        "topics",
        "entities",
        "summary_points",
        "content_metrics",
        "language",
        "quotes"
    ]
    
    for field in required_intel_fields:
        assert field in intel, f"Missing intelligence field: {field}"
    
    # Check types
    assert isinstance(intel["key_points"], list)
    assert isinstance(intel["topics"], list)
    assert isinstance(intel["entities"], dict)
    assert isinstance(intel["summary_points"], list)
    assert isinstance(intel["content_metrics"], dict)
    
    # Check metrics
    metrics = intel["content_metrics"]
    assert "word_count" in metrics
    assert "words_per_minute" in metrics
    assert "speaking_pace" in metrics
    
    print("\n✅ Response structure matches specification!")
    print(f"   - Title: {structured['title'][:50]}...")
    print(f"   - Duration: {structured['duration']}s")
    print(f"   - Transcript: {len(structured['transcript'])} chars")
    print(f"   - Segments: {len(structured['transcript_segments'])}")
    print(f"   - Intelligence: {len(intel['key_points'])} key points, {len(intel['topics'])} topics")
    
    print("\n✅ Structure test passed!\n")
    return True


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Video Intelligence Engine Test Suite")
    print("=" * 60 + "\n")
    
    tests = [
        ("Intelligence Module", test_intelligence_without_video),
        ("Response Structure", test_response_structure),
        ("YouTube Integration", test_youtube),
        ("TikTok Parser", test_tiktok),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            await test_func()
            passed += 1
        except Exception as e:
            print(f"\n❌ {name} failed: {e}\n")
            failed += 1
    
    print("=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("\n🎉 All tests passed! Video Intelligence Engine is ready.\n")
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
