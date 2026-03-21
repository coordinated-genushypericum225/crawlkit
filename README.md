# ⚡ CrawlKit

**Web + Video Intelligence API for AI**

Turn any webpage or video into structured, RAG-ready data. The only crawler that handles both web pages and video transcripts in one API call.

---

## Why CrawlKit?

Every AI agent needs data. But getting clean, structured data from the web is painful:

- Websites use JavaScript rendering, anti-bot protection, dynamic content
- Video content (YouTube, TikTok) is locked inside players with no text extraction
- Generic crawlers return messy HTML/markdown — not structured data
- No tool handles both web AND video in one API

**CrawlKit solves all of this with one API call.**

```python
import httpx

# Crawl a webpage → structured data + RAG chunks
resp = httpx.post("https://api.crawlkit.ai/v1/scrape", json={
    "url": "https://example.com/article",
    "chunk": True
}, headers={"Authorization": "Bearer ck_xxx"})

data = resp.json()["data"]
print(data["content_type"])    # → "news"
print(len(data["chunks"]))     # → 15 RAG-ready chunks
print(data["structured"])      # → Domain-specific metadata

# Same API for video — auto-detects platform
resp = httpx.post("https://api.crawlkit.ai/v1/scrape", json={
    "url": "https://youtube.com/watch?v=abc123"
})

video = resp.json()["data"]
print(video["structured"]["transcript"])  # → Full transcript text
print(video["structured"]["duration"])    # → 1344 (seconds)
print(len(video["chunks"]))              # → 15 transcript chunks
```

## Features

### 🌐 Web Crawling
- **Smart rendering** — Auto-detects static vs JS-heavy pages (httpx → Playwright fallback)
- **Domain-specific parsers** — Legal documents, news articles, real estate listings, financial data
- **Structured extraction** — Not just markdown, but typed fields with metadata
- **Anti-bot handling** — Cloudflare, rate limiting, retry logic built in

### 🎬 Video Crawling
- **YouTube** — Full transcripts (auto-captions), metadata, chapters, tags
- **TikTok** — Captions, hashtags, engagement metrics
- **Facebook Video/Reels** — Metadata + captions when available
- **No video download** — Only extracts text + metadata. Zero bandwidth waste.
- **2-3 seconds** per video regardless of length

### 🧩 RAG-Ready Output
- **Smart chunking** — Legal docs split by Article/Clause, news by paragraph, video by timestamp
- **Token estimation** — Each chunk includes token count for your LLM budget
- **Rich metadata** — Every chunk tagged with source, section, content type
- **Multiple formats** — JSON, Markdown, JSONL, plain text

### 🔍 Auto Detection
CrawlKit automatically identifies content type and applies the right parser:

| Content Type | Sources | What You Get |
|---|---|---|
| **Legal** | Government law databases | Articles, clauses, document metadata, effective dates |
| **News** | News sites | Title, author, date, paragraphs, categories |
| **Real Estate** | Property platforms | Price, area, rooms, location, contact |
| **Finance** | Financial news/data | Stock mentions, categories, market data |
| **Video** | YouTube, TikTok, Facebook | Transcript, duration, views, chapters |
| **Generic** | Any URL | Clean text, markdown, smart chunks |

## API Reference

### `POST /v1/scrape`

Scrape a single URL (web page or video).

```json
{
    "url": "https://example.com/page",
    "parser": null,
    "chunk": true,
    "chunk_max_tokens": 512,
    "formats": ["markdown", "text"],
    "force_js": false,
    "include_html": false
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "url": "https://example.com/page",
        "title": "Page Title",
        "content_type": "news",
        "parser_used": "vnexpress",
        "content_length": 35208,
        "crawl_time_ms": 755,
        "rendered_js": false,
        "markdown": "# Page Title\n\n...",
        "text": "Page Title...",
        "structured": { ... },
        "chunks": [
            {
                "content": "...",
                "metadata": { "title": "...", "section": "..." },
                "index": 0,
                "token_estimate": 487
            }
        ],
        "chunks_count": 15
    }
}
```

### `POST /v1/batch`

Scrape multiple URLs in one request.

```json
{
    "urls": ["https://url1.com", "https://url2.com", "https://youtube.com/watch?v=..."],
    "parser": null,
    "chunk": true,
    "delay": 1.5
}
```

### `POST /v1/discover`

Discover URLs from a source (sitemaps, indexes).

```json
{
    "source": "tvpl",
    "query": "Doanh-nghiep",
    "limit": 100
}
```

### `GET /v1/parsers`

List available domain parsers.

### `GET /v1/health`

Health check + version info.

## Supported Platforms

### Web Parsers
| Parser | Domain | Content |
|---|---|---|
| `tvpl` | thuvienphapluat.vn | Vietnamese legal documents |
| `vbpl` | vbpl.vn | Government legal database |
| `vnexpress` | vnexpress.net | News articles |
| `batdongsan` | batdongsan.com.vn | Real estate listings |
| `cafef` | cafef.vn | Financial news |
| Generic | Any URL | Clean markdown + text |

### Video Parsers
| Parser | Platform | Extracts |
|---|---|---|
| `youtube` | YouTube, youtu.be | Transcript, chapters, metadata, tags |
| `tiktok` | TikTok | Captions, hashtags, engagement |
| `facebook_video` | Facebook, fb.watch | Video metadata, captions |

## Pricing

| Plan | Price | Requests/hr | Batch Size | Features |
|---|---|---|---|---|
| **Free** | $0 | 20 | 5 | All parsers, JSON + Markdown |
| **Starter** | $19/mo | 200 | 50 | + Video transcripts, RAG chunking |
| **Pro** | $79/mo | 2,000 | 500 | + Custom parsers, webhooks, priority support |
| **Enterprise** | Custom | Unlimited | Unlimited | + Dedicated infra, SLA, custom parsers |

## Use Cases

- **AI Agents** — Feed your agent real-time web + video data
- **RAG Pipelines** — Build knowledge bases from websites and YouTube channels  
- **Content Aggregation** — Auto-summarize news, legal updates, market data
- **Research** — Extract and structure data from any source at scale
- **Monitoring** — Track changes on competitor sites, regulations, market trends

## Authentication

All requests require an API key:

```
Authorization: Bearer ck_starter_abc123...
```

Get your free API key at [crawlkit.ai](https://crawlkit.ai)

---

**CrawlKit** — The data layer for AI agents. ⚡
