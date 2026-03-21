"""
Screenshot capture module for web pages.

Features:
- Full-page or viewport-only screenshots
- PNG format with base64 encoding
- Integration with Playwright
"""

from __future__ import annotations
import base64
from typing import Optional, Literal


async def capture_screenshot(
    page,
    full_page: bool = True,
    format: Literal["png", "jpeg"] = "png",
    quality: Optional[int] = None,
) -> dict:
    """
    Capture screenshot of a Playwright page.
    
    Args:
        page: Playwright page object
        full_page: Capture full page (True) or viewport only (False)
        format: Image format (png or jpeg)
        quality: JPEG quality (1-100, only for jpeg)
    
    Returns:
        Dict with screenshot data and metadata
    """
    try:
        # Capture screenshot as bytes
        screenshot_bytes = await page.screenshot(
            full_page=full_page,
            type=format,
            quality=quality if format == "jpeg" else None,
        )
        
        # Encode to base64
        screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
        
        # Get page dimensions
        viewport = page.viewport_size
        
        return {
            "success": True,
            "format": format,
            "full_page": full_page,
            "size_bytes": len(screenshot_bytes),
            "size_kb": round(len(screenshot_bytes) / 1024, 2),
            "base64": screenshot_base64,
            "viewport": viewport,
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Screenshot capture failed: {e}"
        }


def save_screenshot(screenshot_base64: str, output_path: str) -> bool:
    """
    Save base64 screenshot to file.
    
    Args:
        screenshot_base64: Base64-encoded screenshot
        output_path: Path to save file
    
    Returns:
        True if successful
    """
    try:
        screenshot_bytes = base64.b64decode(screenshot_base64)
        with open(output_path, 'wb') as f:
            f.write(screenshot_bytes)
        return True
    except Exception as e:
        print(f"Failed to save screenshot: {e}")
        return False
