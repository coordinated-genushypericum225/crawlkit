"""
CrawlKit — Main crawler class.
Orchestrates fetching, parsing, domain detection, and chunking.
"""

from __future__ import annotations
import time
from typing import Optional, Literal
from urllib.parse import urlparse

from .fetcher import fetch, FetchResult
from .parser import (
    extract_metadata,
    extract_main_content,
    detect_content_type,
)
from .formatter import OutputFormatter
from .chunker import chunk_text
from .result import CrawlResult


class CrawlKit:
    """
    Vietnamese Web Intelligence Crawler.
    
    Usage:
        crawler = CrawlKit()
        result = crawler.scrape("https://thuvienphapluat.vn/van-ban/...")
        print(result.structured)  # Domain-specific structured data
        print(result.chunks)      # RAG-ready chunks
    """
    
    def __init__(
        self,
        js_wait_ms: int = 4000,
        chunk_max_tokens: int = 512,
        chunk_overlap: int = 50,
        auto_chunk: bool = True,
        auto_detect_parser: bool = True,
        learning_engine = None,  # Optional LearningEngine instance
    ):
        self.js_wait_ms = js_wait_ms
        self.chunk_max_tokens = chunk_max_tokens
        self.chunk_overlap = chunk_overlap
        self.auto_chunk = auto_chunk
        self.auto_detect_parser = auto_detect_parser
        self._parsers = self._load_parsers()
        self.learning_engine = learning_engine  # Optional: for self-improving extraction
    
    def _load_parsers(self) -> dict:
        """Load available domain parsers."""
        parsers = {}
        
        try:
            from ..parsers.legal.tvpl import TVPLParser
            parsers["tvpl"] = TVPLParser()
        except ImportError:
            pass
        
        try:
            from ..parsers.legal.vbpl import VBPLParser
            parsers["vbpl"] = VBPLParser()
        except ImportError:
            pass
        
        try:
            from ..parsers.news.vnexpress import VnExpressParser
            parsers["vnexpress"] = VnExpressParser()
        except ImportError:
            pass
        
        try:
            from ..parsers.realestate.batdongsan import BatDongSanParser
            parsers["batdongsan"] = BatDongSanParser()
        except ImportError:
            pass
        
        try:
            from ..parsers.finance.cafef import CafeFParser
            parsers["cafef"] = CafeFParser()
        except ImportError:
            pass
        
        # Video parsers
        try:
            from ..parsers.video.youtube import YouTubeParser
            parsers["youtube"] = YouTubeParser()
        except ImportError:
            pass
        
        try:
            from ..parsers.video.tiktok import TikTokParser
            parsers["tiktok"] = TikTokParser()
        except ImportError:
            pass
        
        try:
            from ..parsers.video.facebook import FacebookVideoParser
            parsers["facebook_video"] = FacebookVideoParser()
        except ImportError:
            pass
        
        # Document parsers
        try:
            from ..parsers.document.pdf import PDFParser
            parsers["pdf"] = PDFParser()
        except ImportError:
            pass
        
        # Code parsers
        try:
            from ..parsers.code.github import GitHubParser
            parsers["github"] = GitHubParser()
        except ImportError:
            pass
        
        return parsers
    
    def _detect_parser(self, url: str) -> Optional[str]:
        """Detect which parser to use based on URL."""
        # Check video platforms first
        if self._is_video_url(url):
            return self._detect_video_parser(url)
        
        domain = urlparse(url).netloc.lower().replace("www.", "")
        
        domain_map = {
            "thuvienphapluat.vn": "tvpl",
            "vbpl.vn": "vbpl",
            "vnexpress.net": "vnexpress",
            "batdongsan.com.vn": "batdongsan",
            "cafef.vn": "cafef",
            "github.com": "github",
        }
        
        return domain_map.get(domain)
    
    def _is_video_url(self, url: str) -> bool:
        """Check if URL is a video platform URL."""
        video_domains = [
            "youtube.com", "youtu.be",
            "tiktok.com", "vm.tiktok.com",
            "facebook.com/watch", "facebook.com/reel",
            "fb.watch",
        ]
        return any(d in url.lower() for d in video_domains)
    
    def _is_pdf_url(self, url: str) -> bool:
        """Check if URL points to a PDF file."""
        url_lower = url.lower()
        # Direct .pdf extension
        if url_lower.endswith('.pdf'):
            return True
        # Common PDF URL patterns (arXiv, etc.)
        pdf_patterns = [
            '/pdf/',  # arXiv: /pdf/1234.5678
            '.pdf?',  # PDFs with query params
        ]
        return any(pattern in url_lower for pattern in pdf_patterns)
    
    def _detect_video_parser(self, url: str) -> Optional[str]:
        """Detect which video parser to use."""
        url_lower = url.lower()
        if "youtube.com" in url_lower or "youtu.be" in url_lower:
            return "youtube"
        if "tiktok.com" in url_lower:
            return "tiktok"
        if "facebook.com" in url_lower or "fb.watch" in url_lower:
            return "facebook_video"
        return None
    
    async def scrape(
        self,
        url: str,
        parser: Optional[str] = None,
        force_js: bool = False,
        force_static: bool = False,
        format: str = "markdown",
        formats: Optional[list[str]] = None,
        chunk: Optional[bool] = None,
        chunk_max_tokens: Optional[int] = None,
        lang: Optional[str] = None,
        intelligence: bool = False,
        auto_extract: bool = False,
        nlp: bool = False,
        ocr: bool = False,
        stealth: bool = False,
        screenshot: bool = False,
    ) -> CrawlResult:
        """
        Scrape a URL and return structured, parsed content.
        
        Args:
            url: URL to scrape
            parser: Force a specific parser (tvpl, vbpl, vnexpress, etc.)
            force_js: Always use Playwright
            force_static: Never use Playwright
            format: Output format (markdown | text | html_clean)
            formats: Legacy - list of formats (deprecated, use format instead)
            chunk: Whether to chunk (None = use auto_chunk setting)
            chunk_max_tokens: Max tokens per chunk
            lang: Preferred subtitle language for videos (e.g., "en", "vi")
            intelligence: Enable video intelligence analysis (video URLs only)
            auto_extract: Use adaptive content extraction (universal parser)
        
        Returns:
            CrawlResult with content, metadata, structured data, and chunks
        """
        start = time.time()
        
        # Use new single format parameter if provided, otherwise fall back to formats list
        if formats is None:
            # New simple format parameter
            output_format = format
        else:
            # Legacy formats list - use first format
            output_format = formats[0] if formats else "markdown"
        
        do_chunk = chunk if chunk is not None else self.auto_chunk
        max_tokens = chunk_max_tokens or self.chunk_max_tokens
        
        # Check if this is a PDF URL — handle differently
        if self._is_pdf_url(url):
            return await self._scrape_pdf(
                url=url,
                output_format=output_format,
                do_chunk=do_chunk,
                max_tokens=max_tokens,
                start=start,
                ocr=ocr,
            )
        
        # Check if this is a video URL — handle differently
        if self._is_video_url(url):
            return self._scrape_video(
                url=url,
                parser=parser,
                output_format=output_format,
                do_chunk=do_chunk,
                max_tokens=max_tokens,
                start=start,
                lang=lang,
                intelligence=intelligence,
            )
        
        # 1. Fetch
        fetch_result = await fetch(
            url,
            force_js=force_js,
            force_static=force_static,
            js_wait_ms=self.js_wait_ms,
        )
        
        if not fetch_result.html or fetch_result.status_code >= 400:
            # Check for detailed error message in headers
            error_msg = fetch_result.headers.get("error", "")
            if error_msg:
                # Provide detailed error from fetcher
                if "playwright_not_installed" in error_msg:
                    error_detail = "Playwright not installed. This site requires JavaScript rendering. Install with: pip install playwright && playwright install chromium"
                elif "chromium_launch_failed" in error_msg:
                    error_detail = f"Chromium browser failed to start (insufficient memory or not installed). This site requires JS rendering but browser cannot launch."
                else:
                    error_detail = f"Fetch error: {error_msg}"
            elif fetch_result.html and "<error>" in fetch_result.html:
                # Extract error from HTML wrapper
                import re
                m = re.search(r'<error>(.+?)</error>', fetch_result.html)
                error_detail = m.group(1) if m else f"Fetch failed: status {fetch_result.status_code}"
            else:
                error_detail = f"Fetch failed: status {fetch_result.status_code}"
            
            return CrawlResult(
                url=url,
                final_url=fetch_result.final_url,
                status_code=fetch_result.status_code,
                error=error_detail,
                crawl_time_ms=int((time.time() - start) * 1000),
                rendered_js=fetch_result.rendered_js,
            )
        
        # 2. Extract main content
        main_html = extract_main_content(fetch_result.html)
        
        # 3. Detect content type
        content_type = detect_content_type(url, fetch_result.html)
        
        # 4. Format content using the specified format
        metadata = extract_metadata(fetch_result.html, url)
        title = metadata.get("title", "")
        
        # Format the main content using OutputFormatter
        content = OutputFormatter.format(main_html, output_format, base_url=url)
        
        # For backward compatibility, populate the appropriate field
        markdown = ""
        text = ""
        html = ""
        
        if output_format == "markdown":
            markdown = content
        elif output_format == "text":
            text = content
        elif output_format == "html_clean":
            html = content
        
        # 5. Check for learned pattern first (fastest, high accuracy)
        parser_name = parser or (self._detect_parser(url) if self.auto_detect_parser else None)
        structured = {}
        extraction_confidence = 0.0
        used_learned_pattern = False
        
        if self.learning_engine and not parser:
            # Try to use learned pattern (skip if parser is explicitly requested)
            learned_pattern = self.learning_engine.get_pattern(url, fetch_result.html)
            if learned_pattern:
                # Use learned pattern — fastest path
                learned_result = self.learning_engine.apply_pattern(fetch_result.html, learned_pattern)
                
                # Use learned content if substantial
                if learned_result.get("content") and len(learned_result["content"]) > 100:
                    content = learned_result["content"]
                    title = learned_result.get("title") or title
                    structured = learned_result.get("extracted", {})
                    extraction_confidence = learned_result.get("extraction_confidence", 0.9)
                    parser_name = learned_result.get("parser_used", "learned")
                    used_learned_pattern = True
                    
                    # Update format-specific fields
                    if output_format == "markdown":
                        markdown = content
                    elif output_format == "text":
                        text = content
                    elif output_format == "html_clean":
                        html = content
        
        # 6. Run domain parser if available (and we didn't use learned pattern)
        if not used_learned_pattern and parser_name and parser_name in self._parsers:
            # Use site-specific parser (highest quality)
            try:
                structured = self._parsers[parser_name].parse(
                    html=fetch_result.html,
                    url=fetch_result.final_url,
                    text=text or markdown,
                )
                # Use parser's title if available
                if structured.get("title"):
                    title = structured["title"]
                
                # Use parser's content if it's richer than generic formatter output
                # (e.g., for listing pages where parser extracts article summaries)
                parser_content = structured.get("content", "")
                if parser_content:
                    # Use parser content if:
                    # 1. It's a listing page, OR
                    # 2. Parser content is significantly richer (>2x length)
                    is_listing = structured.get("page_type") == "listing"
                    is_richer = len(parser_content) > len(content) * 2
                    
                    if is_listing or is_richer:
                        content = parser_content
                        # Update format-specific fields
                        if output_format == "markdown":
                            markdown = content
                        elif output_format == "text":
                            text = content
                        elif output_format == "html_clean":
                            html = content
                
                extraction_confidence = 0.95  # High confidence for site-specific parsers
            except Exception as e:
                structured = {"parser_error": str(e)}
        
        elif auto_extract or (not parser_name and self.auto_detect_parser):
            # Use adaptive extractor as fallback — works on ANY website
            try:
                from ..intelligence import AdaptiveExtractor
                
                extractor = AdaptiveExtractor()
                extraction_result = extractor.extract(
                    html=fetch_result.html,
                    url=fetch_result.final_url,
                )
                
                # Build structured data from extraction
                structured = extraction_result.metadata
                structured["page_type"] = extraction_result.content_type
                
                # Use extracted title if better than generic
                if extraction_result.title and len(extraction_result.title) > len(title):
                    title = extraction_result.title
                
                # Use extracted content
                if extraction_result.content:
                    content = extraction_result.content
                    # Update format-specific fields
                    if output_format == "markdown":
                        markdown = content
                    elif output_format == "text":
                        text = content
                
                extraction_confidence = extraction_result.confidence
                parser_name = "adaptive"
                
            except Exception as e:
                structured = {"adaptive_error": str(e)}
                extraction_confidence = 0.0
        
        # 7. Learn from this crawl (async, non-blocking)
        if self.learning_engine and not used_learned_pattern:
            # Only learn if we didn't use a learned pattern (avoid circular learning)
            quality_score = self._assess_quality({
                "content": content,
                "title": title,
                "content_type": content_type,
                "extraction_confidence": extraction_confidence,
                "extracted": structured,
            })
            
            if quality_score > 0.5:
                try:
                    self.learning_engine.learn_from_crawl(
                        url=fetch_result.final_url,
                        html=fetch_result.html,
                        extraction_result={
                            "content": content,
                            "title": title,
                            "content_type": content_type,
                            "extracted": structured,
                        },
                        quality_score=quality_score,
                    )
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).warning(f"Learning failed: {e}")
            
            # Update domain stats (async, non-blocking)
            try:
                self.learning_engine.update_domain_stats(
                    url=fetch_result.final_url,
                    result={
                        "content": content,
                        "content_type": content_type,
                        "extraction_confidence": quality_score,
                    }
                )
            except Exception:
                pass  # Non-critical, don't log
        
        # 8. Chunk for RAG
        chunks = []
        if do_chunk:
            source_text = text or markdown
            if source_text:
                chunks = chunk_text(
                    source_text,
                    content_type=content_type,
                    max_tokens=max_tokens,
                    overlap=self.chunk_overlap,
                    title=title,
                    metadata={"url": url, "source": parser_name or "generic"},
                )
        
        elapsed = int((time.time() - start) * 1000)
        
        # Store content and format in metadata
        result_metadata = metadata.copy()
        result_metadata["format"] = output_format
        if extraction_confidence > 0:
            result_metadata["extraction_confidence"] = extraction_confidence
        
        # 9. NLP extraction (if requested)
        nlp_result = {}
        if nlp and (text or markdown):
            try:
                from ..nlp import get_extractor
                extractor = get_extractor()
                nlp_content = text or markdown
                nlp_result = extractor.extract(nlp_content)
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"NLP extraction failed: {e}")
        
        return CrawlResult(
            url=url,
            final_url=fetch_result.final_url,
            status_code=fetch_result.status_code,
            title=title,
            markdown=markdown,
            html=html,
            text=text,
            structured=structured,
            metadata=result_metadata,
            chunks=chunks,
            parser_used=parser_name or "generic",
            content_type=content_type,
            crawl_time_ms=elapsed,
            rendered_js=fetch_result.rendered_js,
            entities=nlp_result.get("entities", []),
            keywords=nlp_result.get("keywords", []),
            language=nlp_result.get("language", "unknown"),
        )
    
    def _scrape_video(
        self,
        url: str,
        parser: Optional[str] = None,
        output_format: str = "markdown",
        do_chunk: bool = True,
        max_tokens: int = 512,
        start: float = 0,
        lang: Optional[str] = None,
        intelligence: bool = False,
    ) -> CrawlResult:
        """
        Scrape a video URL — no HTML fetch, uses yt-dlp/transcript API directly.
        
        Args:
            lang: Preferred subtitle language
            intelligence: Enable video intelligence analysis
        """
        parser_name = parser or self._detect_video_parser(url)
        
        if not parser_name or parser_name not in self._parsers:
            return CrawlResult(
                url=url,
                error=f"No video parser available for: {url}",
                crawl_time_ms=int((time.time() - start) * 1000),
            )
        
        try:
            # Pass lang parameter to parser if it supports it
            parser_obj = self._parsers[parser_name]
            if hasattr(parser_obj, 'parse'):
                import inspect
                sig = inspect.signature(parser_obj.parse)
                if 'lang' in sig.parameters:
                    structured = parser_obj.parse(html="", url=url, lang=lang)
                else:
                    structured = parser_obj.parse(html="", url=url)
            else:
                structured = parser_obj.parse(html="", url=url)
        except Exception as e:
            return CrawlResult(
                url=url,
                error=f"Video parsing failed: {e}",
                crawl_time_ms=int((time.time() - start) * 1000),
            )
        
        if structured.get("error"):
            return CrawlResult(
                url=url,
                error=structured["error"],
                crawl_time_ms=int((time.time() - start) * 1000),
            )
        
        title = structured.get("title", "")
        transcript = structured.get("transcript", "")
        description = structured.get("description", "")
        
        # Build text content: transcript + description
        text_parts = []
        if title:
            text_parts.append(f"# {title}")
        if description:
            text_parts.append(f"\n{description}")
        if transcript:
            text_parts.append(f"\n## Transcript\n\n{transcript}")
        
        text = "\n".join(text_parts)
        
        # Build markdown
        md_parts = [f"# {title}"] if title else []
        if structured.get("uploader"):
            md_parts.append(f"**Channel:** {structured['uploader']}")
        if structured.get("upload_date"):
            md_parts.append(f"**Date:** {structured['upload_date']}")
        if structured.get("duration"):
            mins = structured["duration"] // 60
            secs = structured["duration"] % 60
            md_parts.append(f"**Duration:** {mins}:{secs:02d}")
        if structured.get("view_count"):
            md_parts.append(f"**Views:** {structured['view_count']:,}")
        if description:
            md_parts.append(f"\n## Description\n\n{description}")
        if transcript:
            md_parts.append(f"\n## Transcript\n\n{transcript}")
        if structured.get("chapters"):
            md_parts.append("\n## Chapters\n")
            for ch in structured["chapters"]:
                mins = int(ch["start_time"]) // 60
                secs = int(ch["start_time"]) % 60
                md_parts.append(f"- [{mins}:{secs:02d}] {ch['title']}")
        
        markdown = "\n".join(md_parts)
        
        # Determine content type
        content_type = "video"
        source = structured.get("source", parser_name)
        
        # Chunk for RAG
        chunks = []
        if do_chunk and transcript:
            chunks = chunk_text(
                transcript,
                content_type="generic",  # transcript is flowing text
                max_tokens=max_tokens,
                overlap=self.chunk_overlap,
                title=title,
                metadata={
                    "url": url,
                    "source": source,
                    "content_type": "video_transcript",
                    "video_id": structured.get("video_id", ""),
                    "duration": structured.get("duration", 0),
                    "uploader": structured.get("uploader", ""),
                },
            )
        
        # Apply video intelligence if requested
        intelligence_data = None
        if intelligence and transcript:
            from ..intelligence import VideoIntelligence
            
            duration = structured.get("duration", 0)
            intelligence_data = {
                "key_points": VideoIntelligence.extract_key_points(transcript, max_points=5),
                "topics": VideoIntelligence.extract_topics(transcript, max_topics=10),
                "entities": VideoIntelligence.extract_entities(transcript),
                "summary_points": VideoIntelligence.generate_summary_points(transcript, max_points=5),
                "content_metrics": VideoIntelligence.calculate_content_metrics(transcript, duration),
                "language": VideoIntelligence.detect_language(transcript),
                "quotes": VideoIntelligence.extract_quotes(transcript, max_quotes=5),
            }
            # Add intelligence to structured data
            structured["intelligence"] = intelligence_data
        
        elapsed = int((time.time() - start) * 1000)
        
        # Build metadata
        result_metadata = {
            "title": title,
            "source": source,
            "content_type": "video",
            "duration": structured.get("duration", 0),
            "format": output_format,
        }
        if intelligence_data:
            result_metadata["intelligence"] = intelligence_data
        
        return CrawlResult(
            url=url,
            final_url=url,
            status_code=200,
            title=title,
            markdown=markdown,
            text=text,
            structured=structured,
            metadata=result_metadata,
            chunks=chunks,
            parser_used=parser_name,
            content_type="video",
            crawl_time_ms=elapsed,
            rendered_js=False,
        )
    
    async def _scrape_pdf(
        self,
        url: str,
        output_format: str = "markdown",
        do_chunk: bool = True,
        max_tokens: int = 512,
        start: float = 0,
        ocr: bool = False,
    ) -> CrawlResult:
        """
        Scrape a PDF URL — downloads PDF binary and extracts text.
        
        Args:
            url: PDF URL
            output_format: Output format (markdown | text | html_clean)
            do_chunk: Whether to chunk content
            max_tokens: Max tokens per chunk
            start: Start time for elapsed calculation
        
        Returns:
            CrawlResult with PDF content and metadata
        """
        if "pdf" not in self._parsers:
            return CrawlResult(
                url=url,
                error="PDF parser not available. Install with: pip install PyMuPDF",
                crawl_time_ms=int((time.time() - start) * 1000),
            )
        
        try:
            # Use PDF parser
            pdf_parser = self._parsers["pdf"]
            structured = pdf_parser.parse(html="", url=url, ocr=ocr)
            
            if structured.get("error"):
                return CrawlResult(
                    url=url,
                    error=structured["error"],
                    crawl_time_ms=int((time.time() - start) * 1000),
                )
            
            # Extract basic info
            title = structured.get("title", "")
            full_text = structured.get("full_text", "")
            
            # Format content based on output format
            if output_format == "markdown":
                content = pdf_parser.format_markdown(structured)
            elif output_format == "text":
                content = full_text
            else:  # html_clean
                content = structured.get("content", "")
            
            # Populate format-specific fields
            markdown = content if output_format == "markdown" else ""
            text = content if output_format == "text" else full_text
            html = content if output_format == "html_clean" else ""
            
            # Chunk for RAG
            chunks = []
            if do_chunk and full_text:
                chunks = chunk_text(
                    full_text,
                    content_type="generic",
                    max_tokens=max_tokens,
                    overlap=self.chunk_overlap,
                    title=title,
                    metadata={
                        "url": url,
                        "source": "pdf",
                        "content_type": "pdf",
                        "page_count": structured.get("page_count", 0),
                        "author": structured.get("author", ""),
                    },
                )
            
            elapsed = int((time.time() - start) * 1000)
            
            # Build metadata
            result_metadata = {
                "title": title,
                "source": "pdf",
                "content_type": "pdf",
                "format": output_format,
                "author": structured.get("author", ""),
                "page_count": structured.get("page_count", 0),
                "word_count": structured.get("total_words", 0),
                "creation_date": structured.get("creation_date", ""),
            }
            
            # Include warning if present
            if structured.get("warning"):
                result_metadata["warning"] = structured["warning"]
            
            return CrawlResult(
                url=url,
                final_url=url,
                status_code=200,
                title=title,
                markdown=markdown,
                text=text,
                html=html,
                structured=structured,
                metadata=result_metadata,
                chunks=chunks,
                parser_used="pdf",
                content_type="pdf",
                crawl_time_ms=elapsed,
                rendered_js=False,
            )
        
        except Exception as e:
            return CrawlResult(
                url=url,
                error=f"PDF parsing failed: {e}",
                crawl_time_ms=int((time.time() - start) * 1000),
            )
    
    async def batch_scrape(
        self,
        urls: list[str],
        parser: Optional[str] = None,
        delay: float = 1.5,
        **kwargs,
    ) -> list[CrawlResult]:
        """
        Scrape multiple URLs with rate limiting.
        
        Args:
            urls: List of URLs
            parser: Force parser for all
            delay: Seconds between requests
            **kwargs: Passed to scrape()
        """
        import asyncio
        results = []
        for i, url in enumerate(urls):
            result = await self.scrape(url, parser=parser, **kwargs)
            results.append(result)
            
            if i < len(urls) - 1 and delay > 0:
                await asyncio.sleep(delay)
        
        return results
    
    def _assess_quality(self, result: dict) -> float:
        """
        Assess extraction quality 0.0-1.0.
        
        Used by learning engine to decide if a pattern is worth learning.
        Higher score = better extraction = worth learning from.
        """
        score = 0.0
        
        # Has content?
        content = result.get('content', '')
        if len(content) > 100:
            score += 0.3
        if len(content) > 500:
            score += 0.1
        
        # Has title?
        if result.get('title'):
            score += 0.15
        
        # Has metadata?
        extracted = result.get('extracted', {})
        if extracted.get('author'):
            score += 0.1
        if extracted.get('published_date'):
            score += 0.1
        
        # Content type detected?
        if result.get('content_type') and result.get('content_type') != 'generic':
            score += 0.1
        
        # High extraction confidence?
        if result.get('extraction_confidence', 0) > 0.7:
            score += 0.15
        
        return min(score, 1.0)
    
    def discover(
        self,
        domain: str,
        query: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict]:
        """
        Discover URLs from a domain/source.
        
        Args:
            domain: Source identifier (tvpl, vnexpress, batdongsan, etc.)
            query: Search query
            limit: Max URLs to return
        """
        if domain in self._parsers and hasattr(self._parsers[domain], "discover"):
            return self._parsers[domain].discover(query=query, limit=limit)
        
        raise ValueError(f"Discovery not supported for domain: {domain}")
