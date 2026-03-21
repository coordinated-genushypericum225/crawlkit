"""
OCR Module for scanned PDFs.

Uses EasyOCR for text extraction from images.
"""

from __future__ import annotations
from typing import Optional
import io


class OCREngine:
    """OCR engine for extracting text from images."""
    
    def __init__(self):
        self._reader = None
        self._languages = ['vi', 'en']  # Vietnamese and English
    
    def _get_reader(self):
        """Lazy-load EasyOCR reader."""
        if self._reader is None:
            try:
                import easyocr
                print(f"🔍 Loading EasyOCR with languages: {self._languages}")
                self._reader = easyocr.Reader(self._languages, gpu=False)
                print("✅ EasyOCR loaded successfully")
            except ImportError:
                raise ImportError(
                    "EasyOCR not installed. Install with: pip install easyocr"
                )
        return self._reader
    
    def extract_text_from_image(self, image_bytes: bytes) -> str:
        """
        Extract text from image bytes.
        
        Args:
            image_bytes: Image data (PNG, JPEG, etc.)
        
        Returns:
            Extracted text
        """
        reader = self._get_reader()
        
        # Convert bytes to PIL Image
        try:
            from PIL import Image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Run OCR
            results = reader.readtext(image, detail=0)
            
            # Join results
            return "\n".join(results)
        
        except Exception as e:
            print(f"⚠️ OCR failed: {e}")
            return ""
    
    def extract_text_from_pdf_page(self, pdf_page) -> str:
        """
        Extract text from a PyMuPDF page using OCR.
        
        Args:
            pdf_page: fitz.Page object
        
        Returns:
            Extracted text
        """
        try:
            # Render page to image (PNG)
            pix = pdf_page.get_pixmap(dpi=300)  # High DPI for better OCR
            image_bytes = pix.tobytes("png")
            
            # Run OCR
            return self.extract_text_from_image(image_bytes)
        
        except Exception as e:
            print(f"⚠️ Page OCR failed: {e}")
            return ""
    
    def is_scanned_pdf_page(self, page_text: str, image_count: int) -> bool:
        """
        Detect if a PDF page is scanned (image-only).
        
        Args:
            page_text: Extracted text from page
            image_count: Number of images on page
        
        Returns:
            True if page appears to be scanned
        """
        # If page has images but very little text, it's likely scanned
        word_count = len(page_text.split())
        
        # Heuristic: less than 20 words but has images = scanned
        return word_count < 20 and image_count > 0


# Global singleton
_ocr_engine = None

def get_ocr_engine() -> OCREngine:
    """Get or create global OCR engine."""
    global _ocr_engine
    if _ocr_engine is None:
        _ocr_engine = OCREngine()
    return _ocr_engine
