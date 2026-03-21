"""
Parser for thuvienphapluat.vn (TVPL) — Vietnam's largest legal document database.

Handles:
- Legal document metadata extraction (số hiệu, ngày, cơ quan, loại, tình trạng)
- Article (Điều) extraction with chapter/section context
- Related document links
- TVPL's redirect traps and ID mapping

Known issues:
- TVPL redirects wrong IDs to random documents (no error)
- Some pages are behind Cloudflare challenge
- Content is server-rendered in #divContentDoc
"""

from __future__ import annotations
import re
from typing import Any, Optional
from bs4 import BeautifulSoup

from ..base import BaseParser


class TVPLParser(BaseParser):
    name = "tvpl"
    domain = "thuvienphapluat.vn"
    
    def parse(self, html: str, url: str = "", text: str = "") -> dict[str, Any]:
        """Parse a TVPL legal document page."""
        soup = BeautifulSoup(html, "lxml")
        
        result = {
            "source": "tvpl",
            "url": url,
        }
        
        # 1. Extract title
        title_tag = soup.find("title")
        result["title"] = title_tag.string.strip() if title_tag and title_tag.string else ""
        # Clean TVPL title suffix
        result["title"] = re.sub(r'\s*[-–|].*$', '', result["title"]).strip()
        
        # 2. Extract content from main div
        content_div = soup.select_one("#divContentDoc")
        if content_div:
            content_text = content_div.get_text(separator="\n", strip=True)
        else:
            content_text = text or ""
        
        result["content"] = content_text
        result["content_length"] = len(content_text)
        
        # 3. Extract metadata from content header
        result.update(self._extract_legal_metadata(content_text, soup))
        
        # 4. Extract articles (Điều)
        articles = self._extract_articles(content_text)
        result["articles"] = articles
        result["articles_count"] = len(articles)
        
        # 5. Extract chapters
        chapters = self._extract_chapters(content_text)
        result["chapters"] = chapters
        
        # 6. Extract TVPL-specific metadata from sidebar
        result.update(self._extract_sidebar_metadata(soup))
        
        # 7. Related documents
        result["related_docs"] = self._extract_related_docs(soup)
        
        # 8. Verify correct document (detect redirect trap)
        result["redirect_verified"] = self._verify_no_redirect(url, result)
        
        return result
    
    def _extract_legal_metadata(self, text: str, soup: BeautifulSoup) -> dict:
        """Extract legal metadata: số hiệu, ngày, cơ quan, etc."""
        meta = {}
        
        # Số hiệu (document number)
        patterns = [
            r'(?:Số|Luật số|Nghị định số|Thông tư số|Quyết định số)[:\s]+([^\n]+)',
            r'(?:số\s+)(\d+/\d{4}/[A-ZĐ\-]+)',
        ]
        for p in patterns:
            m = re.search(p, text[:2000])
            if m:
                meta["so_hieu"] = m.group(1).strip().rstrip(",.")
                break
        
        # Loại văn bản
        loai_map = {
            "Luật": r'\bLUẬT\b',
            "Bộ luật": r'\bBỘ LUẬT\b',
            "Nghị định": r'\bNGHỊ ĐỊNH\b',
            "Thông tư": r'\bTHÔNG TƯ\b',
            "Quyết định": r'\bQUYẾT ĐỊNH\b',
            "Chỉ thị": r'\bCHỈ THỊ\b',
            "Công văn": r'\bCÔNG VĂN\b',
            "Nghị quyết": r'\bNGHỊ QUYẾT\b',
        }
        for loai, pattern in loai_map.items():
            if re.search(pattern, text[:3000]):
                meta["loai_van_ban"] = loai
                break
        
        # Ngày ban hành
        date_match = re.search(
            r'ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})',
            text[:3000]
        )
        if date_match:
            d, m, y = date_match.group(1), date_match.group(2), date_match.group(3)
            meta["ngay_ban_hanh"] = f"{y}-{m.zfill(2)}-{d.zfill(2)}"
        
        # Cơ quan ban hành
        co_quan_patterns = [
            r'(QUỐC HỘI)',
            r'(CHÍNH PHỦ)',
            r'(THỦ TƯỚNG CHÍNH PHỦ)',
            r'(BỘ [A-ZĐÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴ\s]+)',
            r'(ỦY BAN NHÂN DÂN[^\n]*)',
            r'(HỘI ĐỒNG NHÂN DÂN[^\n]*)',
        ]
        for p in co_quan_patterns:
            m = re.search(p, text[:1000])
            if m:
                meta["co_quan_ban_hanh"] = m.group(1).strip()
                break
        
        return meta
    
    def _extract_articles(self, text: str) -> list[dict]:
        """Extract individual articles (Điều) from legal text."""
        articles = []
        
        dieu_pattern = re.compile(
            r'(Điều\s+(\d+[a-z]?)\.?\s*([^\n]*))',
            re.MULTILINE
        )
        
        matches = list(dieu_pattern.finditer(text))
        
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            
            content = text[start:end].strip()
            
            articles.append({
                "number": match.group(2),
                "title": match.group(3).strip().rstrip("."),
                "content": content,
                "content_length": len(content),
            })
        
        return articles
    
    def _extract_chapters(self, text: str) -> list[dict]:
        """Extract chapters (Chương) from legal text."""
        chapters = []
        
        chuong_pattern = re.compile(
            r'Chương\s+([IVXLCDM\d]+)\s*\n?\s*([A-ZĐÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴ,\s]+)',
            re.MULTILINE
        )
        
        for match in chuong_pattern.finditer(text):
            chapters.append({
                "number": match.group(1),
                "title": match.group(2).strip(),
            })
        
        return chapters
    
    def _extract_sidebar_metadata(self, soup: BeautifulSoup) -> dict:
        """Extract metadata from TVPL sidebar (tình trạng, hiệu lực, etc.)."""
        meta = {}
        
        # Tình trạng hiệu lực
        status_el = soup.select_one('.hieuluc, .status, [class*="hieu-luc"]')
        if status_el:
            meta["tinh_trang"] = status_el.get_text(strip=True)
        
        # Look for metadata table
        for row in soup.select('.doc-info tr, .vanBanInfo tr, .attribute'):
            cells = row.find_all(['td', 'th', 'span', 'div'])
            if len(cells) >= 2:
                key = cells[0].get_text(strip=True).lower()
                val = cells[1].get_text(strip=True)
                
                if "hiệu lực" in key:
                    meta["tinh_trang"] = val
                elif "ngày hiệu lực" in key or "có hiệu lực" in key:
                    meta["ngay_hieu_luc"] = val
                elif "lĩnh vực" in key:
                    meta["linh_vuc"] = val
                elif "người ký" in key:
                    meta["nguoi_ky"] = val
        
        return meta
    
    def _extract_related_docs(self, soup: BeautifulSoup) -> list[dict]:
        """Extract related document links."""
        related = []
        
        for a in soup.select('a[href*="/van-ban/"]'):
            href = a.get("href", "")
            text = a.get_text(strip=True)
            
            if text and len(text) > 10 and "/van-ban/" in href:
                if not href.startswith("http"):
                    href = f"https://thuvienphapluat.vn{href}"
                
                # Extract doc ID
                id_match = re.search(r'-(\d+)\.aspx', href)
                doc_id = id_match.group(1) if id_match else None
                
                related.append({
                    "title": text[:120],
                    "url": href.split("?")[0],
                    "doc_id": doc_id,
                })
        
        # Deduplicate
        seen = set()
        unique = []
        for doc in related:
            key = doc.get("doc_id") or doc["url"]
            if key not in seen:
                seen.add(key)
                unique.append(doc)
        
        return unique[:50]  # Limit to 50
    
    def _verify_no_redirect(self, original_url: str, result: dict) -> bool:
        """
        Verify TVPL didn't redirect to a different document.
        TVPL silently redirects invalid IDs to random documents.
        """
        if not original_url or not result.get("title"):
            return False
        
        # Extract expected info from URL
        url_parts = original_url.split("/")[-1].replace(".aspx", "").split("-")
        
        # Simple heuristic: check if URL keywords appear in title
        title_lower = result["title"].lower()
        url_keywords = [p.lower() for p in url_parts if len(p) > 3 and not p.isdigit()]
        
        if url_keywords:
            matches = sum(1 for k in url_keywords[:3] if k in title_lower)
            return matches > 0
        
        return True
    
    def discover(self, query: Optional[str] = None, limit: int = 100) -> list[dict]:
        """
        Discover legal document URLs from TVPL sitemap.
        
        Args:
            query: Filter by keyword (e.g., "Doanh-nghiep")
            limit: Max URLs to return
        """
        import httpx
        from bs4 import BeautifulSoup as BS
        
        headers = {"User-Agent": "Mozilla/5.0 (compatible; CrawlKit/0.1)"}
        results = []
        
        # Scan sitemaps
        for i in range(1, 568):
            if len(results) >= limit:
                break
            
            try:
                r = httpx.get(
                    f"https://thuvienphapluat.vn/resitemap{i}.xml",
                    headers=headers,
                    timeout=10,
                )
                soup = BS(r.text, "xml")
                
                for url_tag in soup.find_all("url"):
                    loc = url_tag.find("loc")
                    if loc:
                        u = loc.text
                        if "/van-ban/" in u:
                            if not query or query.lower() in u.lower():
                                results.append({
                                    "url": u,
                                    "source": "tvpl_sitemap",
                                })
                                if len(results) >= limit:
                                    break
            except Exception:
                continue
        
        return results
