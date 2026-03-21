"""
Noise Filter - Advanced HTML cleaning.

Removes non-content elements more intelligently than basic HTML stripping.
Better than html2text for extracting clean content.
"""

from __future__ import annotations
import re
from bs4 import BeautifulSoup, Tag
from typing import Optional


class NoiseFilter:
    """Remove non-content elements from HTML."""
    
    # Elements to always remove
    REMOVE_TAGS = [
        'script', 'style', 'noscript', 'iframe', 'svg', 'canvas',
        'video', 'audio', 'embed', 'object', 'param',
    ]
    
    # Class/ID patterns that indicate noise (English)
    NOISE_PATTERNS = [
        r'nav(?!igation-content)',  # nav, navbar, navigation (but not navigation-content)
        r'menu',
        r'sidebar',
        r'footer',
        r'header(?![-_]?(?:image|img|photo))',  # header but not header-image
        r'ad(?:s|vertis)?(?:[-_]?(?:banner|container|wrapper|section))?',
        r'banner(?![-_]?image)',
        r'social',
        r'share',
        r'comment(?:s|[-_]section)?',
        r'related(?![-_]?(?:content|article))',  # related but allow related-content
        r'recommend(?:ed)?',
        r'popular',
        r'trending',
        r'widget',
        r'popup',
        r'modal',
        r'overlay',
        r'cookie',
        r'newsletter',
        r'subscribe',
        r'signup',
        r'login',
        r'breadcrumb',
        r'pagination',
        r'pager',
        r'print',
        r'email',
        r'bookmark',
        r'save',
        r'toolbar',
        r'masthead',
        r'promo',
    ]
    
    # Vietnamese-specific noise patterns
    VN_NOISE = [
        r'tin[-_]?lien[-_]?quan',      # related news
        r'bai[-_]?viet[-_]?lien[-_]?quan',  # related articles
        r'doc[-_]?them',                # read more
        r'binh[-_]?luan',               # comments
        r'chia[-_]?se',                 # share
        r'theo[-_]?doi',                # follow
        r'quang[-_]?cao',               # advertisement
        r'tai[-_]?tro',                 # sponsored
        r'khuyen[-_]?mai',              # promotion
        r'dang[-_]?ky',                 # sign up
        r'dang[-_]?nhap',               # login
    ]
    
    def __init__(self):
        """Initialize noise filter with compiled patterns."""
        # Combine all patterns
        all_patterns = self.NOISE_PATTERNS + self.VN_NOISE
        
        # Compile regex for efficiency
        self._noise_regex = re.compile(
            '|'.join(f'({p})' for p in all_patterns),
            re.IGNORECASE
        )
    
    def clean(self, soup: BeautifulSoup) -> BeautifulSoup:
        """
        Remove all noise elements from soup.
        
        Args:
            soup: BeautifulSoup object (will be modified in place)
            
        Returns:
            Cleaned BeautifulSoup object
        """
        # Make a copy to avoid modifying original
        soup = BeautifulSoup(str(soup), 'lxml')
        
        # Remove by tag
        self._remove_by_tag(soup)
        
        # Remove by class/id pattern
        self._remove_by_pattern(soup)
        
        # Remove short text blocks
        self._remove_short_text_blocks(soup, min_words=5)
        
        # Remove high link density blocks
        self._remove_high_link_density(soup, threshold=0.5)
        
        # Remove empty elements
        self._remove_empty_elements(soup)
        
        return soup
    
    def _remove_by_tag(self, soup: BeautifulSoup) -> None:
        """Remove elements by tag name."""
        for tag_name in self.REMOVE_TAGS:
            for tag in soup.find_all(tag_name):
                tag.decompose()
    
    def _remove_by_pattern(self, soup: BeautifulSoup) -> None:
        """Remove elements matching noise patterns in class/id."""
        for tag in soup.find_all(True):  # Find all tags
            # Skip if tag has no attrs (can happen during decomposition)
            if not hasattr(tag, 'attrs') or tag.attrs is None:
                continue
            
            # Check class attribute
            classes = tag.get('class', [])
            if classes:
                class_str = ' '.join(classes)
                if self._noise_regex.search(class_str):
                    tag.decompose()
                    continue
            
            # Check id attribute
            tag_id = tag.get('id', '')
            if tag_id and self._noise_regex.search(tag_id):
                tag.decompose()
                continue
            
            # Check role attribute
            role = tag.get('role', '')
            if role in ['navigation', 'banner', 'complementary', 'contentinfo']:
                tag.decompose()
                continue
    
    def _remove_short_text_blocks(self, soup: BeautifulSoup, min_words: int = 5) -> None:
        """
        Remove blocks with very few words (likely navigation).
        
        Args:
            soup: BeautifulSoup object
            min_words: Minimum words to keep a block
        """
        # Target block-level elements
        block_tags = ['div', 'section', 'aside', 'nav', 'header', 'footer']
        
        for tag in soup.find_all(block_tags):
            text = tag.get_text(strip=True)
            word_count = len(text.split())
            
            # Remove if too short and doesn't contain important nested content
            if word_count < min_words:
                # Check if it has nested article/main content
                if not tag.find(['article', 'main']):
                    # Check if all children are also short
                    has_long_child = False
                    for child in tag.find_all(block_tags):
                        child_text = child.get_text(strip=True)
                        if len(child_text.split()) >= min_words * 2:
                            has_long_child = True
                            break
                    
                    if not has_long_child:
                        tag.decompose()
    
    def _remove_high_link_density(self, soup: BeautifulSoup, threshold: float = 0.5) -> None:
        """
        Remove blocks where >50% of text is links (navigation areas).
        
        Args:
            soup: BeautifulSoup object
            threshold: Max ratio of link text to total text (0.0-1.0)
        """
        block_tags = ['div', 'section', 'aside', 'nav', 'ul', 'ol']
        
        for tag in soup.find_all(block_tags):
            # Get total text length
            total_text = tag.get_text(strip=True)
            total_len = len(total_text)
            
            if total_len == 0:
                continue
            
            # Get link text length
            link_text = ' '.join(a.get_text(strip=True) for a in tag.find_all('a'))
            link_len = len(link_text)
            
            # Calculate link density
            link_density = link_len / total_len if total_len > 0 else 0
            
            # Remove if too many links and block is small/medium
            if link_density > threshold and total_len < 500:
                # Don't remove if it's the only content on page
                body = soup.find('body')
                if body and len(body.get_text(strip=True)) > total_len * 2:
                    tag.decompose()
    
    def _remove_empty_elements(self, soup: BeautifulSoup) -> None:
        """Remove elements with no text content."""
        # Don't remove self-closing tags like img, br, hr
        skip_tags = {'img', 'br', 'hr', 'input', 'meta', 'link'}
        
        for tag in soup.find_all(True):
            if tag.name in skip_tags:
                continue
            
            # Check if element has text or contains images
            has_text = bool(tag.get_text(strip=True))
            has_img = bool(tag.find('img'))
            
            if not has_text and not has_img:
                tag.decompose()
    
    def get_clean_text(self, soup: BeautifulSoup) -> str:
        """
        Get clean text from soup after removing noise.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Clean text string
        """
        cleaned = self.clean(soup)
        text = cleaned.get_text(separator='\n', strip=True)
        
        # Remove excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        
        return text.strip()
