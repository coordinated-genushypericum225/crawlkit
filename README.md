<p align="center">
  <img src="https://crawlkit.org/img/og-cover.png" alt="CrawlKit" width="600">
</p>

<h1 align="center">CrawlKit</h1>

<p align="center">
  <strong>Open-source web + video crawling toolkit for AI</strong>
</p>

<p align="center">
  <a href="https://github.com/Paparusi/crawlkit/stargazers"><img src="https://img.shields.io/github/stars/Paparusi/crawlkit?style=social" alt="Stars"></a>
  <a href="https://github.com/Paparusi/crawlkit/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-blue.svg" alt="License"></a>
  <a href="https://pypi.org/project/crawlkit/"><img src="https://img.shields.io/pypi/v/crawlkit?color=blue" alt="PyPI"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python"></a>
  <a href="https://hub.docker.com/r/paparusi/crawlkit"><img src="https://img.shields.io/badge/docker-ready-2496ED.svg" alt="Docker"></a>
  <a href="https://github.com/Paparusi/crawlkit/actions/workflows/ci.yml"><img src="https://github.com/Paparusi/crawlkit/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
</p>

<p align="center">
  <a href="#-quickstart">Quickstart</a> •
  <a href="#-features">Features</a> •
  <a href="#-why-crawlkit">Why CrawlKit</a> •
  <a href="#-api-reference">API</a> •
  <a href="#-self-hosting">Self-Host</a> •
  <a href="https://crawlkit.org">Managed API →</a>
</p>

---

## 🤔 Why CrawlKit?

Every AI app needs web data. But current tools force you to choose: **web OR video, fast OR accurate, simple OR powerful.**

CrawlKit does it all in one API call:

```python
from crawlkit import CrawlKit

ck = CrawlKit()

# Webpage → structured data + RAG chunks
page = ck.scrape("https://vnexpress.net/some-article")
print(page.content_type)   # "news"
print(page.chunks)         # 15 RAG-ready chunks

# Video → transcript + metadata (same API!)
video = ck.scrape("https://youtube.com/watch?v=abc123")
print(video.transcript)    # Full text transcript
print(video.duration)      # 1344 seconds
```

## ⚡ Why not Crawl4AI / Firecrawl / Jina?

| Feature | CrawlKit | Crawl4AI | Firecrawl | Jina Reader |
|---|:---:|:---:|:---:|:---:|
| Web crawling | ✅ | ✅ | ✅ | ✅ |
| **YouTube transcripts** | ✅ | ❌ | ❌ | ❌ |
| **TikTok extraction** | ✅ | ❌ | ❌ | ❌ |
| **Facebook Video** | ✅ | ❌ | ❌ | ❌ |
| **PDF + OCR** | ✅ | ❌ | ✅ | ❌ |
| **NLP extraction** | ✅ | ❌ | ❌ | ❌ |
| Anti-bot stealth | ✅ | ✅ | ✅ | ❌ |
| Screenshot capture | ✅ | ✅ | ✅ | ❌ |
| RAG-ready chunks | ✅ | ❌ | ✅ | ❌ |
| Domain-specific parsers | ✅ 10+ | ❌ | ❌ | ❌ |
| URL monitoring | ✅ | ❌ | ❌ | ❌ |
| Self-hostable | ✅ | ✅ | ❌ | ❌ |
| Open source | ✅ Apache 2.0 | ✅ | ❌ | ❌ |

**TL;DR:** CrawlKit = Crawl4AI + video support + OCR + NLP + domain parsers.

## 🚀 Quickstart

### Option 1: pip install

```bash
pip install crawlkit
playwright install chromium
```

```python
from crawlkit import CrawlKit

ck = CrawlKit()

# Any webpage
result = ck.scrape("https://example.com")
print(result.markdown)

# YouTube video → transcript
result = ck.scrape("https://youtube.com/watch?v=dQw4w9WgXcQ")
print(result.transcript)

# With RAG chunking
result = ck.scrape("https://example.com", chunk=True)
for chunk in result.chunks:
    print(f"[{chunk.token_estimate} tokens] {chunk.content[:80]}...")
```

### Option 2: Docker (self-host API)

```bash
git clone https://github.com/Paparusi/crawlkit.git
cd crawlkit
cp .env.example .env

docker compose up -d
# API available at http://localhost:8000
```

### Option 3: Managed API

No setup needed. Get a free API key at **[crawlkit.org](https://crawlkit.org)**

```bash
curl -X POST https://api.crawlkit.org/v1/scrape \
  -H "Authorization: Bearer ck_free_xxx" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtube.com/watch?v=abc123"}'
```

## ✨ Features

### 🌐 Web Crawling
- **Smart rendering** — Auto-detects static vs JS-heavy pages (httpx → Playwright fallback)
- **Anti-bot stealth** — Playwright-stealth, random fingerprints, human-like delays
- **Domain parsers** — 10+ site-specific parsers for structured extraction
- **Batch crawling** — Scrape hundreds of URLs in one request

### 🎬 Video Intelligence
- **YouTube** — Full transcripts, chapters, metadata, tags (2-3s per video)
- **TikTok** — Captions, hashtags, engagement metrics
- **Facebook Video** — Metadata + captions
- **No video download** — Text extraction only. Zero bandwidth waste.

### 🧠 AI-Ready Output
- **RAG chunks** — Smart chunking by content type (legal → by article, news → by paragraph)
- **NLP extraction** — Entities (people, orgs, locations) + keywords
- **Token estimation** — Each chunk tagged with token count
- **Multiple formats** — JSON, Markdown, plain text

### 📸 OCR + PDF
- **PDF parsing** — Text, tables, metadata extraction
- **Scanned PDF → text** — Auto-detect + OCR (EasyOCR)
- **50MB max** — Handles large documents

### 📷 Screenshot + Monitoring
- **Full-page screenshots** — PNG/JPEG, viewport or full-page
- **URL monitoring** — Watch pages for changes, webhook notifications
- **Change detection** — SHA256 hash comparison

## 🔌 Domain Parsers

CrawlKit auto-detects the site and applies the right parser:

| Parser | Site | What You Get |
|---|---|---|
| `youtube` | YouTube | Transcript, chapters, duration, views, tags |
| `tiktok` | TikTok | Caption, hashtags, music, engagement |
| `facebook_video` | Facebook | Video metadata, captions |
| `tvpl` | thuvienphapluat.vn | Legal documents, articles, clauses |
| `vbpl` | vbpl.vn | Government legal database |
| `vnexpress` | vnexpress.net | News articles, clean text |
| `batdongsan` | batdongsan.com.vn | Property listings, prices |
| `cafef` | cafef.vn | Financial news, stock data |
| `github` | github.com | Repo/file content |
| `pdf` | Any .pdf URL | Text, tables, metadata |
| _Generic_ | Any URL | Clean markdown + structured data |

> **Building a custom parser?** See [CONTRIBUTING.md](CONTRIBUTING.md) — PRs welcome!

## 📡 API Reference

### `POST /v1/scrape` — Scrape a URL

```bash
curl -X POST http://localhost:8000/v1/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://youtube.com/watch?v=abc123",
    "chunk": true,
    "nlp": true,
    "stealth": false,
    "screenshot": false,
    "ocr": false
  }'
```

<details>
<summary>📦 Response</summary>

```json
{
  "success": true,
  "data": {
    "url": "https://youtube.com/watch?v=abc123",
    "title": "Video Title",
    "content_type": "video",
    "parser_used": "youtube",
    "crawl_time_ms": 2150,
    "markdown": "# Video Title\n\n...",
    "structured": {
      "transcript": "Full transcript text...",
      "duration": 1344,
      "views": 125000,
      "chapters": [...]
    },
    "chunks": [
      {
        "content": "...",
        "metadata": {"timestamp": "00:00", "section": "intro"},
        "token_estimate": 487
      }
    ],
    "nlp": {
      "language": "vi",
      "entities": {"people": [], "organizations": [], "locations": []},
      "keywords": ["keyword1", "keyword2"]
    }
  }
}
```
</details>

### `POST /v1/batch` — Batch scrape

```json
{
  "urls": ["https://url1.com", "https://url2.com"],
  "chunk": true,
  "delay": 1.5
}
```

### `POST /v1/discover` — Discover URLs from a site

```json
{
  "source": "tvpl",
  "query": "Doanh-nghiep",
  "limit": 100
}
```

### `POST /v1/screenshot` — Capture screenshot

```json
{
  "url": "https://example.com",
  "full_page": true,
  "format": "png"
}
```

### `POST /v1/watch` — Monitor URL for changes

```json
{
  "url": "https://example.com/page",
  "webhook_url": "https://your-server.com/webhook",
  "check_interval_minutes": 60
}
```

### `GET /v1/health` • `GET /v1/parsers`

## 🐳 Self-Hosting

```bash
git clone https://github.com/Paparusi/crawlkit.git
cd crawlkit
cp .env.example .env
# Edit .env with your config

docker compose up -d
```

The API runs at `http://localhost:8000`. No external dependencies required.

<details>
<summary>📋 Environment Variables</summary>

```env
# Required
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
CRAWLKIT_MASTER_KEY=your-master-key

# Optional
PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
PORT=8000
```
</details>

## ☁️ Managed API

Don't want to self-host? Use the managed API at **[crawlkit.org](https://crawlkit.org)**

| Plan | Price | Requests/day | Features |
|---|---|---|---|
| **Free** | $0 | 100 | All parsers, all formats |
| **Starter** | $19/mo | 2,000 | + Video, OCR, NLP, stealth |
| **Pro** | $79/mo | 20,000 | + Batch, monitoring, priority |
| **Enterprise** | Custom | Unlimited | + Dedicated infra, SLA |

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Easy wins:**
- Add a new domain parser (see `crawlkit/parsers/` for examples)
- Improve extraction quality for existing parsers
- Add tests
- Fix bugs from [Issues](https://github.com/Paparusi/crawlkit/issues)

## 📄 License

Apache 2.0 — Use it however you want. See [LICENSE](LICENSE).

## ⭐ Star History

If CrawlKit helps your project, give it a star! It helps others discover the project.

[![Star History Chart](https://api.star-history.com/svg?repos=Paparusi/crawlkit&type=Date)](https://star-history.com/#Paparusi/crawlkit&Date)

---

<p align="center">
  <strong>Built with ❤️ for the AI community</strong>
  <br>
  <a href="https://crawlkit.org">Website</a> •
  <a href="https://github.com/Paparusi/crawlkit/issues">Issues</a> •
  <a href="https://github.com/Paparusi/crawlkit/discussions">Discussions</a>
</p>
