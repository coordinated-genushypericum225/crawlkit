# PDF Parser Guide

## Overview

CrawlKit now supports PDF document parsing! Extract text, metadata, tables, and page-by-page content from any PDF file via URL.

## Features

✅ **Text Extraction** - Full text extraction from all pages  
✅ **Metadata** - Title, author, creation date, page count, word count  
✅ **Page-by-Page** - Individual page text, word counts, image detection  
✅ **Table Detection** - Automatic table extraction (PyMuPDF 1.23+)  
✅ **Format Support** - Markdown, text, or HTML output  
✅ **RAG-Ready Chunks** - Automatic chunking for vector embeddings  
✅ **Edge Cases** - Password protection, scanned PDFs, size limits, corrupted files  

## Installation

```bash
pip install PyMuPDF>=1.23.0
```

Already included in `requirements.txt`.

## Usage

### Python API

```python
from crawlkit import CrawlKit

crawler = CrawlKit()

# Basic PDF scrape
result = await crawler.scrape("https://arxiv.org/pdf/1706.03762")

print(result.title)                    # Document title
print(result.text)                     # Full extracted text
print(result.structured['page_count']) # Number of pages
print(result.structured['author'])     # Document author
print(result.chunks)                   # RAG-ready chunks

# Markdown format
result = await crawler.scrape(
    "https://example.com/document.pdf",
    format="markdown"
)
print(result.markdown)  # Nicely formatted markdown with metadata
```

### REST API

```bash
# Basic scrape
curl -X POST https://crawlkit.paparusi.workers.dev/v1/scrape \
  -H "Authorization: Bearer ck_free_YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://arxiv.org/pdf/1706.03762"
  }'

# Markdown format
curl -X POST https://crawlkit.paparusi.workers.dev/v1/scrape \
  -H "Authorization: Bearer ck_free_YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/document.pdf",
    "format": "markdown"
  }'
```

### Response Structure

```json
{
  "success": true,
  "data": {
    "title": "Attention Is All You Need",
    "content": "full extracted text...",
    "content_type": "pdf",
    "content_length": 45000,
    "parser_used": "pdf",
    "structured": {
      "source": "pdf",
      "url": "https://arxiv.org/pdf/1706.03762",
      "title": "",
      "author": "",
      "creation_date": "2017-06-12 17:57:34",
      "page_count": 15,
      "total_words": 6095,
      "total_chars": 39821,
      "total_images": 3,
      "pages": [
        {
          "page": 1,
          "text": "Page 1 content...",
          "word_count": 450,
          "char_count": 2850,
          "images": 0,
          "tables": []
        }
      ],
      "full_text": "Complete document text...",
      "content": "Formatted content...",
      "content_length": 45000
    },
    "chunks": [
      {
        "text": "Chunk 1 content...",
        "metadata": {
          "url": "https://arxiv.org/pdf/1706.03762",
          "source": "pdf",
          "content_type": "pdf",
          "page_count": 15
        }
      }
    ]
  }
}
```

## Edge Cases Handled

### Password-Protected PDFs
```json
{
  "success": false,
  "error": "PDF is password protected"
}
```

### Scanned PDFs (Image-Only)
```json
{
  "success": true,
  "data": {
    "structured": {
      "warning": "PDF contains scanned images, text extraction may be incomplete"
    }
  }
}
```

### Large PDFs (>50MB)
```json
{
  "success": false,
  "error": "PDF too large (65.3MB), max 50MB"
}
```

### Corrupted PDFs
```json
{
  "success": false,
  "error": "Corrupted or invalid PDF file"
}
```

### Download Timeout (30s)
```json
{
  "success": false,
  "error": "PDF download timeout after 30 seconds"
}
```

## URL Detection

The parser automatically detects PDF URLs using multiple patterns:

- ✅ `https://example.com/document.pdf` - Direct `.pdf` extension
- ✅ `https://arxiv.org/pdf/1706.03762` - `/pdf/` in path
- ✅ `https://example.com/file.pdf?download=true` - `.pdf` with query params
- ✅ Content-Type: `application/pdf` header check

## Format Options

### Markdown (default)
```python
result = await crawler.scrape(url, format="markdown")
# result.markdown contains formatted content with metadata header
```

**Example output:**
```markdown
# Document Title

**Author:** John Doe  
**Created:** 2025-01-15 10:30:45  
**Pages:** 15  
**Words:** 8,500

---

## Page 1

[page 1 content...]

## Page 2

[page 2 content...]
```

### Text
```python
result = await crawler.scrape(url, format="text")
# result.text contains raw extracted text
```

**Example output:**
```
Page 1 content...

Page 2 content...
```

### HTML Clean
```python
result = await crawler.scrape(url, format="html_clean")
# result.html contains formatted HTML
```

## Table Extraction

If PyMuPDF 1.23+ is installed, tables are automatically detected and extracted:

```python
result = await crawler.scrape("https://example.com/report.pdf")

for page in result.structured['pages']:
    for table in page['tables']:
        print(f"Table with {table['rows']} rows × {table['cols']} cols")
        print(table['data'][:5])  # First 5 rows
```

## RAG Integration

PDFs are automatically chunked for vector embeddings:

```python
result = await crawler.scrape(
    "https://arxiv.org/pdf/1706.03762",
    chunk=True,
    chunk_max_tokens=512
)

# Use chunks for vector DB
for chunk in result.chunks:
    embedding = embed(chunk['text'])
    vector_db.insert(embedding, metadata=chunk['metadata'])
```

## Performance

- **Small PDFs (<1MB):** ~1-2 seconds
- **Medium PDFs (1-10MB):** ~3-8 seconds
- **Large PDFs (10-50MB):** ~10-30 seconds

Processing time depends on:
- File size
- Network speed (download time)
- Number of pages
- Text density
- Table complexity

## Testing

Tested with:
- ✅ Simple PDFs (W3C dummy.pdf)
- ✅ Academic papers (arXiv - Attention Is All You Need)
- ✅ Multi-page documents (15+ pages)
- ✅ Various formats (text, markdown, html)
- ✅ Chunking for RAG

## Limitations

- **Max size:** 50MB
- **Timeout:** 30 seconds download
- **Scanned PDFs:** Limited text extraction (image-based content)
- **Password-protected:** Not supported
- **Complex layouts:** May lose some formatting
- **Tables:** Best effort extraction (requires PyMuPDF 1.23+)

## Next Steps

Future enhancements:
- [ ] OCR support for scanned PDFs (Tesseract integration)
- [ ] Better table extraction and formatting
- [ ] Image extraction and description
- [ ] PDF form field extraction
- [ ] Multi-language support improvements
- [ ] Streaming for very large PDFs

---

**Questions?** Open an issue on GitHub or contact support.
