"""
Output formatters for CrawlKit.
Converts HTML to different output formats: markdown, text, html_clean.
"""

from __future__ import annotations
import re
from bs4 import BeautifulSoup
import html2text


class OutputFormatter:
    """Format HTML content into different output formats."""
    
    @staticmethod
    def format(html: str, format_type: str = "markdown", base_url: str = "") -> str:
        """
        Convert HTML to the specified format.
        
        Args:
            html: Raw HTML content
            format_type: Output format (markdown | text | html_clean)
            base_url: Base URL for resolving relative links
        
        Returns:
            Formatted content string
        """
        if format_type == "text":
            return OutputFormatter.to_text(html)
        elif format_type == "html_clean":
            return OutputFormatter.to_clean_html(html)
        else:  # markdown (default)
            return OutputFormatter.to_markdown(html, base_url)
    
    @staticmethod
    def to_markdown(html: str, base_url: str = "") -> str:
        """
        Convert HTML to clean markdown.
        
        Features:
        - Proper markdown syntax (headings, lists, links, bold, italic)
        - No text wrapping (body_width=0)
        - Protected links [text](url)
        - Unicode support
        - Code blocks preserved
        - Images removed (keep [alt text] only)
        """
        h = html2text.HTML2Text()
        
        # Configuration for clean markdown
        h.body_width = 0              # No line wrapping
        h.protect_links = True        # Don't break URLs
        h.unicode_snob = True         # Use unicode instead of ASCII
        h.ignore_images = True        # Remove images (keep alt text)
        h.ignore_emphasis = False     # Keep bold/italic
        h.skip_internal_links = False # Keep all links
        h.inline_links = True         # [text](url) format instead of references
        h.mark_code = True            # Preserve code blocks
        
        if base_url:
            h.baseurl = base_url
        
        # Convert to markdown
        md = h.handle(html)
        
        # Post-processing cleanup
        # Remove excessive blank lines (3+ → 2)
        md = re.sub(r"\n{3,}", "\n\n", md)
        
        # Remove leading/trailing whitespace
        md = md.strip()
        
        # Fix malformed lists (ensure proper spacing)
        md = re.sub(r'\n([*-]) ', r'\n\n\1 ', md)  # Add blank line before list
        
        return md
    
    @staticmethod
    def to_text(html: str) -> str:
        """
        Convert HTML to plain text.
        
        Features:
        - Strip all HTML tags
        - Remove formatting (no markdown syntax)
        - Clean text only
        - Paragraphs separated by double newlines
        - Remove scripts, styles, nav, footer, etc.
        """
        soup = BeautifulSoup(html, "lxml")
        
        # Remove unwanted elements
        noise_tags = [
            "script", "style", "nav", "footer", "header", "aside",
            "noscript", "iframe", "form", "input", "button"
        ]
        for tag_name in noise_tags:
            for tag in soup.find_all(tag_name):
                tag.decompose()
        
        # Extract text with separators
        text = soup.get_text(separator="\n", strip=True)
        
        # Cleanup
        # Remove excessive blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)
        
        # Remove leading/trailing whitespace per line
        lines = [line.strip() for line in text.split("\n")]
        text = "\n".join(lines)
        
        # Final trim
        text = text.strip()
        
        return text
    
    @staticmethod
    def to_clean_html(html: str) -> str:
        """
        Clean HTML - keep semantic tags only.
        
        Keeps:
        - Semantic tags: h1-h6, p, a, ul, ol, li, strong, em, code, pre, table, tr, td, th, blockquote
        - Content structure
        
        Removes:
        - Scripts, styles, tracking pixels
        - Navigation, footer, header, aside, iframe
        - Forms, inputs, buttons
        - Classes, IDs, style attributes (keep href only)
        - Ads, tracking elements
        """
        soup = BeautifulSoup(html, "lxml")
        
        # 1. Remove unwanted tags entirely
        unwanted_tags = [
            "script", "style", "nav", "footer", "header", "aside",
            "noscript", "iframe", "form", "input", "button", "select",
            "textarea", "label", "fieldset", "legend",
            "svg", "canvas", "video", "audio", "embed", "object"
        ]
        for tag_name in unwanted_tags:
            for tag in soup.find_all(tag_name):
                tag.decompose()
        
        # 2. Remove elements by class/id (ads, tracking)
        ad_selectors = [
            "[class*='ad-']", "[class*='ads-']", "[class*='advertisement']",
            "[id*='ad-']", "[id*='ads-']",
            "[class*='promo']", "[class*='banner']",
            "[class*='sponsor']", "[class*='tracking']"
        ]
        for selector in ad_selectors:
            try:
                for el in soup.select(selector):
                    el.decompose()
            except Exception:
                pass
        
        # 3. Whitelist of semantic tags to keep
        allowed_tags = {
            "h1", "h2", "h3", "h4", "h5", "h6",
            "p", "a", "span", "div",
            "ul", "ol", "li",
            "strong", "b", "em", "i",
            "code", "pre",
            "table", "tr", "td", "th", "thead", "tbody",
            "blockquote", "br", "hr"
        }
        
        # 4. Remove disallowed tags (unwrap content)
        for tag in soup.find_all():
            if tag.name not in allowed_tags:
                tag.unwrap()
        
        # 5. Clean attributes - keep only href for links
        for tag in soup.find_all():
            # Keep href for <a> tags
            if tag.name == "a" and tag.has_attr("href"):
                href = tag["href"]
                tag.attrs.clear()
                tag["href"] = href
            else:
                # Remove all attributes
                tag.attrs.clear()
        
        # 6. Get clean HTML
        clean_html = str(soup)
        
        # 7. Post-processing cleanup
        # Remove empty tags
        clean_html = re.sub(r'<(\w+)>\s*</\1>', '', clean_html)
        
        # Remove excessive whitespace
        clean_html = re.sub(r'\n{3,}', '\n\n', clean_html)
        
        # Trim
        clean_html = clean_html.strip()
        
        return clean_html


# Convenience functions for backward compatibility
def html_to_markdown(html: str, base_url: str = "") -> str:
    """Convert HTML to markdown (backward compatible)."""
    return OutputFormatter.to_markdown(html, base_url)


def html_to_text(html: str) -> str:
    """Convert HTML to text (backward compatible)."""
    return OutputFormatter.to_text(html)


def html_to_clean_html(html: str) -> str:
    """Convert HTML to clean semantic HTML."""
    return OutputFormatter.to_clean_html(html)
