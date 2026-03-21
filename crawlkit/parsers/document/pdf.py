"""
Parser for PDF documents.

Extracts:
- Text content from all pages
- Metadata (title, author, creation date)
- Page-by-page breakdown
- Tables (if available)
"""

from __future__ import annotations
import io
import re
from typing import Any, Optional
from datetime import datetime

from ..base import BaseParser


class PDFParser(BaseParser):
    """Extract structured content from PDF files."""
    
    name = "pdf"
    domain = "pdf"
    
    # Maximum PDF size: 50MB
    MAX_SIZE_BYTES = 50 * 1024 * 1024
    
    # Download timeout: 30 seconds
    DOWNLOAD_TIMEOUT = 30
    
    def can_handle(self, url: str) -> bool:
        """Check if URL points to a PDF file."""
        return url.lower().endswith('.pdf') or 'application/pdf' in url.lower()
    
    def parse(self, html: str = "", url: str = "", text: str = "", ocr: bool = False) -> dict[str, Any]:
        """
        Download and parse PDF from URL.
        
        Args:
            html: Ignored for PDF parser
            url: URL to PDF file
            text: Ignored for PDF parser
            ocr: Enable OCR for scanned PDFs
        
        Returns:
            Dict with PDF content and metadata
        """
        if not url:
            return {"error": "PDF URL is required"}
        
        try:
            # Download PDF binary
            import httpx
            
            response = httpx.get(
                url,
                timeout=self.DOWNLOAD_TIMEOUT,
                follow_redirects=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            )
            
            # Check Content-Type to confirm it's actually a PDF
            content_type = response.headers.get("content-type", "").lower()
            if "application/pdf" not in content_type and not url.lower().endswith('.pdf'):
                return {"error": f"URL does not point to a PDF file (Content-Type: {content_type})"}
            
            # Check file size
            pdf_bytes = response.content
            if len(pdf_bytes) > self.MAX_SIZE_BYTES:
                size_mb = len(pdf_bytes) / (1024 * 1024)
                return {"error": f"PDF too large ({size_mb:.1f}MB), max 50MB"}
            
            # Parse PDF
            return self.parse_bytes(pdf_bytes, url=url, ocr=ocr)
        
        except httpx.TimeoutException:
            return {"error": f"PDF download timeout after {self.DOWNLOAD_TIMEOUT} seconds"}
        except httpx.HTTPError as e:
            return {"error": f"HTTP error downloading PDF: {e}"}
        except Exception as e:
            return {"error": f"Failed to download PDF: {e}"}
    
    def parse_bytes(self, pdf_bytes: bytes, url: str = "", ocr: bool = False) -> dict[str, Any]:
        """
        Parse PDF from bytes.
        
        Args:
            pdf_bytes: PDF file content
            url: Source URL (optional)
            ocr: Enable OCR for scanned PDFs
        
        Returns:
            Dict with extracted text, metadata, pages
        """
        try:
            import fitz  # PyMuPDF
        except ImportError:
            return {
                "error": "PyMuPDF not installed. Install with: pip install PyMuPDF"
            }
        
        try:
            # Open PDF from bytes
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            # Check if password-protected
            if doc.needs_pass:
                doc.close()
                return {"error": "PDF is password protected"}
            
            # Extract metadata
            metadata = doc.metadata or {}
            
            result = {
                "source": "pdf",
                "url": url,
                "title": metadata.get("title", ""),
                "author": metadata.get("author", ""),
                "subject": metadata.get("subject", ""),
                "creator": metadata.get("creator", ""),
                "producer": metadata.get("producer", ""),
                "creation_date": self._parse_pdf_date(metadata.get("creationDate", "")),
                "modification_date": self._parse_pdf_date(metadata.get("modDate", "")),
                "page_count": len(doc),
                "pages": [],
                "full_text": "",
            }
            
            # Extract text from each page
            all_text = []
            total_images = 0
            ocr_used = False
            
            # Load OCR engine if needed
            ocr_engine = None
            if ocr:
                try:
                    from .ocr import get_ocr_engine
                    ocr_engine = get_ocr_engine()
                except ImportError:
                    print("⚠️ OCR requested but easyocr not installed")
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Extract text
                page_text = page.get_text("text")
                
                # Count images to detect scanned PDFs
                images = page.get_images()
                image_count = len(images)
                total_images += image_count
                
                # If OCR enabled and page appears scanned, run OCR
                if ocr_engine and ocr_engine.is_scanned_pdf_page(page_text, image_count):
                    try:
                        ocr_text = ocr_engine.extract_text_from_pdf_page(page)
                        if ocr_text:
                            page_text = ocr_text
                            ocr_used = True
                            print(f"✅ OCR applied to page {page_num + 1}")
                    except Exception as e:
                        print(f"⚠️ OCR failed on page {page_num + 1}: {e}")
                
                all_text.append(page_text)
                
                # Extract tables (if PyMuPDF supports it - version 1.23+)
                tables = []
                try:
                    if hasattr(page, "find_tables"):
                        table_finder = page.find_tables()
                        for table in table_finder.tables:
                            # Extract table as list of rows
                            table_data = table.extract()
                            if table_data:
                                tables.append({
                                    "rows": len(table_data),
                                    "cols": len(table_data[0]) if table_data else 0,
                                    "data": table_data[:10],  # First 10 rows only
                                })
                except Exception:
                    # Table extraction not available or failed
                    pass
                
                result["pages"].append({
                    "page": page_num + 1,
                    "text": page_text,
                    "word_count": len(page_text.split()),
                    "char_count": len(page_text),
                    "images": image_count,
                    "tables": tables,
                })
            
            # Add OCR flag to result
            if ocr_used:
                result["ocr_applied"] = True
            
            # Combine all text
            result["full_text"] = "\n\n".join(all_text)
            result["total_words"] = len(result["full_text"].split())
            result["total_chars"] = len(result["full_text"])
            result["total_images"] = total_images
            
            # Build content for display
            result["content"] = self._format_content(result)
            result["content_length"] = len(result["content"])
            
            # Check if this is a scanned PDF (image-only)
            avg_words_per_page = result["total_words"] / max(result["page_count"], 1)
            if avg_words_per_page < 50 and total_images > result["page_count"]:
                result["warning"] = "PDF contains scanned images, text extraction may be incomplete"
            
            doc.close()
            return result
        
        except fitz.FileDataError:
            return {"error": "Corrupted or invalid PDF file"}
        except Exception as e:
            return {"error": f"PDF parsing failed: {e}"}
    
    def _parse_pdf_date(self, date_str: str) -> str:
        """
        Parse PDF date format (D:YYYYMMDDHHmmSS) to ISO format.
        
        Args:
            date_str: PDF date string
        
        Returns:
            ISO formatted date or empty string
        """
        if not date_str:
            return ""
        
        # PDF date format: D:YYYYMMDDHHmmSS+HH'mm'
        # Example: D:20250115103045+07'00'
        match = re.match(r"D:(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})", date_str)
        if match:
            try:
                year, month, day, hour, minute, second = match.groups()
                dt = datetime(
                    int(year), int(month), int(day),
                    int(hour), int(minute), int(second)
                )
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass
        
        return date_str
    
    def _format_content(self, result: dict) -> str:
        """
        Format PDF content for display.
        
        Args:
            result: Parsed PDF result dict
        
        Returns:
            Formatted content string
        """
        parts = []
        
        # Title and metadata
        if result.get("title"):
            parts.append(f"# {result['title']}\n")
        
        if result.get("author"):
            parts.append(f"**Author:** {result['author']}")
        
        if result.get("creation_date"):
            parts.append(f"**Created:** {result['creation_date']}")
        
        if result.get("page_count"):
            parts.append(f"**Pages:** {result['page_count']}")
        
        if result.get("total_words"):
            parts.append(f"**Words:** {result['total_words']:,}")
        
        parts.append("")  # Blank line
        
        # Full text
        if result.get("full_text"):
            parts.append(result["full_text"])
        
        return "\n".join(parts)
    
    def format_markdown(self, result: dict) -> str:
        """
        Format PDF content as markdown with page breaks.
        
        Args:
            result: Parsed PDF result dict
        
        Returns:
            Markdown formatted content
        """
        parts = []
        
        # Header with metadata
        if result.get("title"):
            parts.append(f"# {result['title']}\n")
        
        metadata_parts = []
        if result.get("author"):
            metadata_parts.append(f"**Author:** {result['author']}")
        if result.get("subject"):
            metadata_parts.append(f"**Subject:** {result['subject']}")
        if result.get("creation_date"):
            metadata_parts.append(f"**Created:** {result['creation_date']}")
        if result.get("page_count"):
            metadata_parts.append(f"**Pages:** {result['page_count']}")
        if result.get("total_words"):
            metadata_parts.append(f"**Words:** {result['total_words']:,}")
        
        if metadata_parts:
            parts.append("  \n".join(metadata_parts))
            parts.append("\n---\n")
        
        # Page-by-page content
        for page in result.get("pages", []):
            page_num = page.get("page", 1)
            page_text = page.get("text", "")
            
            if page_text.strip():
                parts.append(f"## Page {page_num}\n")
                parts.append(page_text)
                parts.append("")  # Blank line between pages
        
        return "\n".join(parts)
    
    def can_parse(self, url: str) -> bool:
        """Check if this parser can handle the given URL."""
        return self.can_handle(url)
