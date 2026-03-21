#!/usr/bin/env python3
"""
Comprehensive test of Adaptive Content Extraction Engine.
Tests all major components.
"""

import asyncio
from bs4 import BeautifulSoup
from crawlkit.intelligence import AdaptiveExtractor, NoiseFilter, SchemaParser


def test_noise_filter():
    """Test the noise filter."""
    print("\n" + "="*80)
    print("Testing NoiseFilter")
    print("="*80)
    
    html = """
    <html>
        <head><title>Test Page</title></head>
        <body>
            <nav class="navbar">Navigation</nav>
            <div class="sidebar">Sidebar content</div>
            <article>
                <h1>Main Article</h1>
                <p>This is the main content of the article.</p>
                <p>It has multiple paragraphs.</p>
            </article>
            <div class="comments">
                <div class="comment">Comment 1</div>
                <div class="comment">Comment 2</div>
            </div>
            <footer>Footer content</footer>
        </body>
    </html>
    """
    
    soup = BeautifulSoup(html, 'lxml')
    filter = NoiseFilter()
    
    clean = filter.clean(soup)
    clean_text = filter.get_clean_text(soup)
    
    # Verify noise was removed
    assert "Navigation" not in clean_text, "Navigation should be removed"
    assert "Sidebar content" not in clean_text, "Sidebar should be removed"
    assert "Footer content" not in clean_text, "Footer should be removed"
    assert "Comment 1" not in clean_text, "Comments should be removed"
    
    # Verify main content is preserved
    assert "Main Article" in clean_text, "Main article title should be preserved"
    assert "main content" in clean_text, "Main content should be preserved"
    
    print("✓ NoiseFilter works correctly")
    print(f"  Original length: {len(soup.get_text())}")
    print(f"  Clean length: {len(clean_text)}")
    print(f"  Clean text: {clean_text[:200]}")


def test_schema_parser():
    """Test the schema parser."""
    print("\n" + "="*80)
    print("Testing SchemaParser")
    print("="*80)
    
    html = """
    <html>
        <head>
            <title>Test Article</title>
            <meta property="og:title" content="Article Title">
            <meta property="og:description" content="Article description">
            <meta property="og:type" content="article">
            <meta property="article:published_time" content="2026-03-19">
            <meta name="author" content="John Doe">
            <script type="application/ld+json">
            {
                "@context": "https://schema.org",
                "@type": "Article",
                "headline": "Test Article",
                "author": {
                    "@type": "Person",
                    "name": "Jane Smith"
                },
                "datePublished": "2026-03-19"
            }
            </script>
        </head>
        <body>
            <article itemscope itemtype="http://schema.org/Product">
                <h1 itemprop="name">Product Name</h1>
                <meta itemprop="price" content="99.99">
            </article>
        </body>
    </html>
    """
    
    soup = BeautifulSoup(html, 'lxml')
    parser = SchemaParser()
    
    # Test individual extractors
    og = parser.extract_opengraph(soup)
    assert og.get("title") == "Article Title", "OpenGraph title should be extracted"
    assert og.get("type") == "article", "OpenGraph type should be extracted"
    
    meta = parser.extract_meta(soup)
    assert meta.get("author") == "John Doe", "Author meta should be extracted"
    assert meta.get("published_time") == "2026-03-19", "Published time should be extracted"
    
    jsonld = parser.extract_jsonld(soup)
    assert len(jsonld) == 1, "Should extract 1 JSON-LD object"
    assert jsonld[0]["@type"] == "Article", "JSON-LD type should be Article"
    
    microdata = parser.extract_microdata(soup)
    assert "Product" in microdata, "Should extract Product microdata"
    assert microdata["Product"]["name"] == "Product Name", "Product name should be extracted"
    
    # Test merged data
    merged = parser.merge(soup)
    assert merged.get("title") == "Test Article", "Merged title should prioritize JSON-LD"
    assert merged.get("author") == "Jane Smith", "Merged author should prioritize JSON-LD"
    
    print("✓ SchemaParser works correctly")
    print(f"  Open Graph fields: {list(og.keys())}")
    print(f"  Meta fields: {list(meta.keys())}")
    print(f"  JSON-LD objects: {len(jsonld)}")
    print(f"  Microdata schemas: {list(microdata.keys())}")
    print(f"  Merged title: {merged.get('title')}")


def test_adaptive_extractor():
    """Test the adaptive extractor."""
    print("\n" + "="*80)
    print("Testing AdaptiveExtractor")
    print("="*80)
    
    # Article HTML
    article_html = """
    <html lang="vi">
        <head>
            <title>Test Article - News Site</title>
            <meta property="og:type" content="article">
            <meta property="article:published_time" content="2026-03-19">
            <meta name="author" content="Nguyen Van A">
            <meta name="description" content="This is a test article">
        </head>
        <body>
            <nav>Navigation</nav>
            <article>
                <h1>Test Article Title</h1>
                <div class="author">By Nguyen Van A</div>
                <time datetime="2026-03-19">19/03/2026</time>
                <p class="summary">This is the summary of the article.</p>
                <div class="content">
                    <p>This is the first paragraph of the article content. It contains meaningful information.</p>
                    <p>This is the second paragraph with more details about the topic.</p>
                    <h2>Section Title</h2>
                    <p>More content in a subsection.</p>
                </div>
                <div class="tags">
                    <a href="#">tag1</a>
                    <a href="#">tag2</a>
                </div>
            </article>
            <div class="sidebar">Sidebar</div>
            <footer>Footer</footer>
        </body>
    </html>
    """
    
    extractor = AdaptiveExtractor()
    result = extractor.extract(article_html, "https://test.com/article/123")
    
    # Verify detection
    assert result.content_type == "article", f"Should detect article, got {result.content_type}"
    assert result.title == "Test Article Title", f"Should extract title, got {result.title}"
    assert result.confidence > 0.5, f"Confidence should be >0.5, got {result.confidence}"
    
    # Verify extracted fields
    assert result.metadata.get("author") == "Nguyen Van A", "Should extract author"
    assert result.metadata.get("published_date"), "Should extract published date"
    assert result.metadata.get("summary"), "Should extract summary (first paragraph or explicit summary)"
    assert "first paragraph" in result.metadata.get("content", "") or "summary" in result.metadata.get("content", "").lower(), "Should extract content"
    
    print("✓ AdaptiveExtractor works correctly")
    print(f"  Content type: {result.content_type}")
    print(f"  Title: {result.title}")
    print(f"  Confidence: {result.confidence:.1%}")
    print(f"  Author: {result.metadata.get('author')}")
    print(f"  Word count: {result.metadata.get('word_count')}")
    print(f"  Language: {result.metadata.get('language')}")


def test_product_extraction():
    """Test product extraction."""
    print("\n" + "="*80)
    print("Testing Product Extraction")
    print("="*80)
    
    product_html = """
    <html>
        <head>
            <title>iPhone 15 Pro - 256GB</title>
            <meta property="og:type" content="product">
        </head>
        <body>
            <div class="product">
                <h1>iPhone 15 Pro</h1>
                <div class="price">25.990.000đ</div>
                <div class="old-price">29.990.000đ</div>
                <div class="description">Flagship smartphone with amazing features</div>
                <div class="specs">
                    <div class="spec-row">
                        <span class="spec-label">Màn hình</span>
                        <span class="spec-value">6.1 inch</span>
                    </div>
                </div>
                <div class="availability">Còn hàng</div>
            </div>
        </body>
    </html>
    """
    
    extractor = AdaptiveExtractor()
    result = extractor.extract(product_html, "https://test.com/product/iphone-15")
    
    assert result.content_type == "product", f"Should detect product, got {result.content_type}"
    assert result.metadata.get("price") is not None, "Should extract price"
    assert result.metadata.get("availability"), "Should extract availability"
    
    print("✓ Product extraction works correctly")
    print(f"  Name: {result.metadata.get('name')}")
    print(f"  Price: {result.metadata.get('price')} {result.metadata.get('currency')}")
    print(f"  Original price: {result.metadata.get('original_price')}")
    print(f"  Discount: {result.metadata.get('discount')}")
    print(f"  Availability: {result.metadata.get('availability')}")


async def main():
    """Run all tests."""
    print("\nCrawlKit Adaptive Content Extraction - Component Tests")
    print("="*80)
    
    try:
        test_noise_filter()
        test_schema_parser()
        test_adaptive_extractor()
        test_product_extraction()
        
        print("\n" + "="*80)
        print("✅ All tests passed!")
        print("="*80)
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
