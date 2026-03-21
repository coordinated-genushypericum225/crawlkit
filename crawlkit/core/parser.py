"""
HTML to clean content parser.
Converts raw HTML to markdown, text, and extracts metadata.
"""

from __future__ import annotations
import re
from bs4 import BeautifulSoup, Tag
import html2text


def html_to_markdown(html: str, base_url: str = "") -> str:
    """Convert HTML to clean markdown."""
    h = html2text.HTML2Text()
    h.body_width = 0  # No wrapping
    h.ignore_links = False
    h.ignore_images = True
    h.ignore_emphasis = False
    h.skip_internal_links = True
    h.inline_links = True
    if base_url:
        h.baseurl = base_url
    
    md = h.handle(html)
    
    # Clean up excessive whitespace
    md = re.sub(r"\n{3,}", "\n\n", md)
    md = md.strip()
    
    return md


def html_to_text(html: str) -> str:
    """Convert HTML to plain text."""
    soup = BeautifulSoup(html, "lxml")
    
    # Remove script, style, nav, footer, header
    for tag in soup.find_all(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
        tag.decompose()
    
    text = soup.get_text(separator="\n", strip=True)
    
    # Clean up
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()
    
    return text


def extract_metadata(html: str, url: str = "") -> dict:
    """Extract metadata from HTML head."""
    soup = BeautifulSoup(html, "lxml")
    meta = {}
    
    # Title
    title_tag = soup.find("title")
    meta["title"] = title_tag.string.strip() if title_tag and title_tag.string else ""
    
    # Meta tags
    for tag in soup.find_all("meta"):
        name = tag.get("name", tag.get("property", "")).lower()
        content = tag.get("content", "")
        if name and content:
            if name in ("description", "og:description"):
                meta["description"] = content
            elif name in ("keywords",):
                meta["keywords"] = [k.strip() for k in content.split(",")]
            elif name in ("og:title",):
                meta.setdefault("title", content)
            elif name in ("og:image",):
                meta["image"] = content
            elif name in ("og:type",):
                meta["type"] = content
            elif name in ("og:url",):
                meta["canonical_url"] = content
            elif name in ("author",):
                meta["author"] = content
            elif name in ("robots",):
                meta["robots"] = content
    
    # Canonical URL
    canonical = soup.find("link", rel="canonical")
    if canonical and canonical.get("href"):
        meta.setdefault("canonical_url", canonical["href"])
    
    # Language
    html_tag = soup.find("html")
    if html_tag and html_tag.get("lang"):
        meta["language"] = html_tag["lang"]
    
    meta["url"] = url
    
    return meta


def extract_main_content(html: str) -> str:
    """Extract the main content area from HTML, removing boilerplate."""
    soup = BeautifulSoup(html, "lxml")
    
    # Remove noise elements
    noise_selectors = [
        "script", "style", "nav", "footer", "header", "aside",
        "noscript", "iframe", ".ads", ".advertisement", ".banner",
        ".sidebar", ".menu", ".nav", ".breadcrumb", ".pagination",
        ".comment", ".comments", ".social", ".share", ".related",
        "#header", "#footer", "#nav", "#sidebar", "#menu",
        "[role='navigation']", "[role='banner']", "[role='complementary']",
    ]
    
    for sel in noise_selectors:
        try:
            for tag in soup.select(sel):
                tag.decompose()
        except Exception:
            pass
    
    # Try to find main content area
    content_selectors = [
        # Vietnamese legal sites
        "#divContentDoc",           # TVPL
        "#ctl00_PlaceHolderMain_ContentPlaceHolderMain_toanvan",  # vbpl.vn
        ".content-doc",
        # News sites
        "article .article-content",
        "article .body",
        ".detail-content",          # VnExpress
        ".detail__content",
        ".content-detail",
        # Generic
        "article",
        "main",
        "[role='main']",
        ".content",
        "#content",
    ]
    
    for sel in content_selectors:
        try:
            el = soup.select_one(sel)
            if el and len(el.get_text(strip=True)) > 200:
                return str(el)
        except Exception:
            pass
    
    # Fallback: return body
    body = soup.find("body")
    return str(body) if body else str(soup)


def detect_content_type(url: str, html: str = "", text: str = "") -> str:
    """Detect the type of content: legal, news, realestate, finance, generic."""
    from urllib.parse import urlparse
    domain = urlparse(url).netloc.lower().replace("www.", "")
    
    # Domain-based detection
    legal_domains = {"thuvienphapluat.vn", "vbpl.vn", "luatvietnam.vn", "congbao.chinhphu.vn", "phapdien.moj.gov.vn"}
    news_domains = {"vnexpress.net", "tuoitre.vn", "thanhnien.vn", "dantri.com.vn", "baochinhphu.vn", "zingnews.vn"}
    realestate_domains = {"batdongsan.com.vn", "homedy.com", "nhadat.cafef.vn", "muaban.net", "alonhadat.com.vn"}
    finance_domains = {"cafef.vn", "vietstock.vn", "stockbiz.vn", "fireant.vn", "simplize.vn"}
    
    if domain in legal_domains:
        return "legal"
    if domain in news_domains:
        return "news"
    if domain in realestate_domains:
        return "realestate"
    if domain in finance_domains:
        return "finance"
    
    # Content-based detection (fallback)
    sample = (text or "")[:2000].lower()
    
    legal_signals = ["điều", "khoản", "nghị định", "thông tư", "luật số", "quyết định", "ban hành", "hiệu lực"]
    news_signals = ["phóng viên", "theo tin", "nguồn tin", "bài viết", "đăng ngày"]
    realestate_signals = ["m²", "phòng ngủ", "giá bán", "giá thuê", "căn hộ", "nhà đất"]
    finance_signals = ["cổ phiếu", "chứng khoán", "VN-Index", "doanh thu", "lợi nhuận"]
    
    scores = {
        "legal": sum(1 for s in legal_signals if s in sample),
        "news": sum(1 for s in news_signals if s in sample),
        "realestate": sum(1 for s in realestate_signals if s in sample),
        "finance": sum(1 for s in finance_signals if s in sample),
    }
    
    best = max(scores, key=scores.get)
    return best if scores[best] >= 2 else "generic"
