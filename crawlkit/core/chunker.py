"""
Vietnamese-aware text chunking for RAG.

Unlike English chunkers that split on sentences/paragraphs,
this understands Vietnamese document structure:
- Legal: split by Điều (Article), Khoản (Clause), Chương (Chapter)
- News: split by paragraphs with heading context
- BĐS: split by listing fields
- Generic: smart paragraph-based with Vietnamese sentence detection
"""

from __future__ import annotations
import re
from typing import Optional


def chunk_text(
    text: str,
    content_type: str = "generic",
    max_tokens: int = 512,
    overlap: int = 50,
    title: str = "",
    metadata: Optional[dict] = None,
) -> list[dict]:
    """
    Chunk text into RAG-ready pieces with Vietnamese awareness.
    
    Returns list of:
        {"content": str, "metadata": dict, "index": int, "token_estimate": int}
    """
    if content_type == "legal":
        return _chunk_legal(text, max_tokens, title, metadata or {})
    elif content_type == "news":
        return _chunk_news(text, max_tokens, title, metadata or {})
    elif content_type == "realestate":
        return _chunk_realestate(text, max_tokens, title, metadata or {})
    else:
        return _chunk_generic(text, max_tokens, overlap, title, metadata or {})


def _estimate_tokens(text: str) -> int:
    """Estimate token count for Vietnamese text.
    Vietnamese is roughly 1 token per 2-3 characters (with diacritics).
    """
    return max(1, len(text) // 3)


def _chunk_legal(text: str, max_tokens: int, title: str, base_meta: dict) -> list[dict]:
    """Chunk legal documents by Điều (Article).
    
    Structure: Chương → Mục → Điều → Khoản
    Each Điều becomes a chunk, with context from parent Chương.
    """
    chunks = []
    
    # Find all Điều boundaries
    dieu_pattern = re.compile(
        r'(Điều\s+\d+[a-z]?\.?\s*[^\n]*)',
        re.MULTILINE
    )
    
    # Find all Chương boundaries for context
    chuong_pattern = re.compile(
        r'(Chương\s+[IVXLCDM\d]+[^\n]*(?:\n[A-ZĐ\s,]+)?)',
        re.MULTILINE
    )
    
    # Build chapter map
    chapters = list(chuong_pattern.finditer(text))
    
    def _get_chapter(pos: int) -> str:
        """Get the chapter name for a position in text."""
        chapter = ""
        for ch in chapters:
            if ch.start() <= pos:
                chapter = ch.group(1).strip()
            else:
                break
        return chapter
    
    # Split by Điều
    dieu_matches = list(dieu_pattern.finditer(text))
    
    if not dieu_matches:
        # No articles found, fall back to generic chunking
        return _chunk_generic(text, max_tokens, 50, title, base_meta)
    
    for i, match in enumerate(dieu_matches):
        start = match.start()
        end = dieu_matches[i + 1].start() if i + 1 < len(dieu_matches) else len(text)
        
        content = text[start:end].strip()
        dieu_title = match.group(1).strip()
        chapter = _get_chapter(start)
        
        # Extract article number
        num_match = re.search(r'Điều\s+(\d+[a-z]?)', dieu_title)
        article_num = num_match.group(1) if num_match else str(i + 1)
        
        # If chunk is too large, split by Khoản
        if _estimate_tokens(content) > max_tokens * 2:
            sub_chunks = _split_by_khoan(content, article_num, chapter, title, base_meta, max_tokens)
            for j, sc in enumerate(sub_chunks):
                sc["index"] = len(chunks)
                chunks.append(sc)
        else:
            chunks.append({
                "content": content,
                "metadata": {
                    **base_meta,
                    "title": title,
                    "article": f"Điều {article_num}",
                    "article_title": dieu_title,
                    "chapter": chapter,
                    "content_type": "legal",
                },
                "index": len(chunks),
                "token_estimate": _estimate_tokens(content),
            })
    
    return chunks


def _split_by_khoan(
    text: str, article_num: str, chapter: str, title: str, base_meta: dict, max_tokens: int
) -> list[dict]:
    """Split a large article by Khoản (Clause)."""
    khoan_pattern = re.compile(r'(\d+\.\s)', re.MULTILINE)
    parts = khoan_pattern.split(text)
    
    chunks = []
    current = ""
    khoan_num = 0
    
    for part in parts:
        if khoan_pattern.match(part):
            if current and _estimate_tokens(current) > 100:
                chunks.append({
                    "content": current.strip(),
                    "metadata": {
                        **base_meta,
                        "title": title,
                        "article": f"Điều {article_num}",
                        "clause": f"Khoản {khoan_num}" if khoan_num else "",
                        "chapter": chapter,
                        "content_type": "legal",
                    },
                    "index": 0,
                    "token_estimate": _estimate_tokens(current),
                })
            current = part
            khoan_num += 1
        else:
            current += part
    
    if current.strip():
        chunks.append({
            "content": current.strip(),
            "metadata": {
                **base_meta,
                "title": title,
                "article": f"Điều {article_num}",
                "clause": f"Khoản {khoan_num}" if khoan_num else "",
                "chapter": chapter,
                "content_type": "legal",
            },
            "index": 0,
            "token_estimate": _estimate_tokens(current),
        })
    
    return chunks


def _chunk_news(text: str, max_tokens: int, title: str, base_meta: dict) -> list[dict]:
    """Chunk news articles by paragraphs with heading context."""
    paragraphs = re.split(r"\n\n+", text)
    
    chunks = []
    current_heading = ""
    buffer = ""
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        # Detect headings (short, bold, or all caps)
        is_heading = (
            len(para) < 100 and
            (para.isupper() or para.startswith("#") or para.startswith("**"))
        )
        
        if is_heading:
            # Flush buffer
            if buffer and _estimate_tokens(buffer) > 50:
                chunks.append({
                    "content": buffer.strip(),
                    "metadata": {
                        **base_meta,
                        "title": title,
                        "section": current_heading,
                        "content_type": "news",
                    },
                    "index": len(chunks),
                    "token_estimate": _estimate_tokens(buffer),
                })
                buffer = ""
            current_heading = para.strip("#* ")
            continue
        
        buffer += "\n\n" + para
        
        if _estimate_tokens(buffer) >= max_tokens:
            chunks.append({
                "content": buffer.strip(),
                "metadata": {
                    **base_meta,
                    "title": title,
                    "section": current_heading,
                    "content_type": "news",
                },
                "index": len(chunks),
                "token_estimate": _estimate_tokens(buffer),
            })
            buffer = ""
    
    # Flush remaining
    if buffer.strip() and _estimate_tokens(buffer) > 50:
        chunks.append({
            "content": buffer.strip(),
            "metadata": {
                **base_meta,
                "title": title,
                "section": current_heading,
                "content_type": "news",
            },
            "index": len(chunks),
            "token_estimate": _estimate_tokens(buffer),
        })
    
    return chunks


def _chunk_realestate(text: str, max_tokens: int, title: str, base_meta: dict) -> list[dict]:
    """Chunk real estate listings — usually 1 listing = 1 chunk."""
    # BĐS listings are usually compact, keep as single chunk
    return [{
        "content": text.strip(),
        "metadata": {
            **base_meta,
            "title": title,
            "content_type": "realestate",
        },
        "index": 0,
        "token_estimate": _estimate_tokens(text),
    }]


def _chunk_generic(
    text: str, max_tokens: int, overlap: int, title: str, base_meta: dict
) -> list[dict]:
    """Generic Vietnamese-aware chunking.
    
    Strategy:
    1. Split on paragraph breaks first (\n\n)
    2. If a paragraph is still too large, split on sentences (. ! ?)
    3. If a sentence is still too large, split on commas/semicolons
    4. Last resort: split on max_chars boundary
    
    This handles:
    - Normal articles (paragraph breaks)
    - Video transcripts (no paragraph breaks, just flowing text)
    - Long single-paragraph text
    """
    if not text or not text.strip():
        return []
    
    max_chars = max_tokens * 3  # ~3 chars per token for Vietnamese
    
    # Step 1: Split into segments (paragraphs → sentences if needed)
    segments = _split_to_segments(text, max_chars)
    
    if not segments:
        return []
    
    # Step 2: Merge segments into chunks respecting max_tokens
    chunks = []
    buffer = ""
    
    for seg in segments:
        seg = seg.strip()
        if not seg:
            continue
        
        candidate = (buffer + " " + seg).strip() if buffer else seg
        
        if _estimate_tokens(candidate) > max_tokens and buffer:
            # Flush current buffer as chunk
            chunks.append(_make_chunk(buffer.strip(), title, base_meta, len(chunks)))
            
            # Overlap: keep tail of previous buffer
            if overlap > 0:
                tail_chars = overlap * 3
                overlap_text = buffer[-tail_chars:].strip()
                # Try to start at a sentence boundary
                dot_pos = overlap_text.find(". ")
                if dot_pos > 0:
                    overlap_text = overlap_text[dot_pos + 2:]
                buffer = (overlap_text + " " + seg).strip()
            else:
                buffer = seg
        else:
            buffer = candidate
    
    # Flush remaining
    if buffer.strip() and _estimate_tokens(buffer) > 30:
        chunks.append(_make_chunk(buffer.strip(), title, base_meta, len(chunks)))
    
    return chunks


def _split_to_segments(text: str, max_chars: int) -> list[str]:
    """Split text into manageable segments.
    
    Hierarchy: paragraphs → sentences → clauses → hard split
    """
    # First split on paragraph breaks
    paragraphs = re.split(r"\n\n+", text)
    
    segments = []
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        if len(para) <= max_chars:
            segments.append(para)
        else:
            # Paragraph too long — split on sentences
            sentences = re.split(r'(?<=[.!?])\s+', para)
            for sent in sentences:
                if len(sent) <= max_chars:
                    segments.append(sent)
                else:
                    # Sentence too long — split on commas/semicolons
                    clauses = re.split(r'(?<=[,;])\s+', sent)
                    for clause in clauses:
                        if len(clause) <= max_chars:
                            segments.append(clause)
                        else:
                            # Hard split at max_chars on word boundary
                            words = clause.split()
                            buf = ""
                            for w in words:
                                if len(buf) + len(w) + 1 > max_chars:
                                    if buf:
                                        segments.append(buf)
                                    buf = w
                                else:
                                    buf = (buf + " " + w) if buf else w
                            if buf:
                                segments.append(buf)
    
    return segments


def _make_chunk(content: str, title: str, base_meta: dict, index: int) -> dict:
    """Create a chunk dict."""
    return {
        "content": content,
        "metadata": {
            **base_meta,
            "title": title,
            "content_type": "generic",
        },
        "index": index,
        "token_estimate": _estimate_tokens(content),
    }
