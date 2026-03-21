# 🚀 CrawlKit — Web + Video Intelligence API cho AI

## Bản tiếng Việt (Viblo / Facebook Dev Groups)

---

### Tiêu đề: Tôi build một API crawler xử lý cả web lẫn video trong 1 lần gọi — và nó miễn phí

---

Chào mọi người,

Mình vừa release **CrawlKit** — một API giúp extract dữ liệu có cấu trúc từ bất kỳ website hay video nào. Viết cho AI agents, nhưng dùng được cho mọi project cần data sạch từ web.

### Vấn đề mình gặp

Khi build ứng dụng AI, mình cần data từ web liên tục:
- Website dùng JS rendering, anti-bot → crawl bình thường không lấy được
- Video trên YouTube/TikTok → nội dung locked trong player, không extract text được  
- Các crawler phổ biến (Scrapy, BeautifulSoup) trả về HTML lộn xộn → phải tự clean
- Không tool nào xử lý **cả web + video** trong 1 API

### CrawlKit giải quyết thế nào?

**1 API call. Tự detect loại content. Trả về structured data.**

```python
import httpx

# Crawl webpage → dữ liệu có cấu trúc
resp = httpx.post("https://api.crawlkit.org/v1/scrape", json={
    "url": "https://vnexpress.net/bai-viet-xyz",
    "chunk": True
}, headers={"X-API-Key": "ck_xxx"})

data = resp.json()["data"]
# content_type: "news"
# title, author, date, content → tự extract
# chunks: 15 đoạn sẵn sàng cho RAG

# Cùng API cho video — tự detect platform
resp = httpx.post("https://api.crawlkit.org/v1/scrape", json={
    "url": "https://youtube.com/watch?v=abc123"
})
# transcript đầy đủ, duration, chapters, metadata
# chunks theo timestamp → feed vào LLM luôn
```

### Tại sao khác biệt?

| | CrawlKit | Firecrawl | Crawl4AI | Jina |
|---|---|---|---|---|
| Web crawling | ✅ | ✅ | ✅ | ✅ |
| **Video crawling** | ✅ | ❌ | ❌ | ❌ |
| RAG chunks | ✅ | ✅ | ✅ | ❌ |
| Vietnamese parsers | ✅ | ❌ | ❌ | ❌ |
| PDF extraction | ✅ | ✅ | ❌ | ❌ |
| Free tier | 100 req/ngày | 500 credits | OSS | 1M tokens |

**Video crawling là điều không ai khác làm.** YouTube, TikTok, Facebook Video — extract transcript + metadata trong 2-3 giây, không cần download video.

### 10+ Smart Parsers

Không chỉ trả HTML/markdown thô. CrawlKit có parser riêng cho từng loại:

- 📰 **VnExpress, CafeF** — tin tức có cấu trúc (title, author, date, body)
- ⚖️ **TVPL, VBPL** — văn bản pháp luật (số hiệu, điều khoản, ngày hiệu lực)
- 🏠 **Batdongsan** — bất động sản (giá, diện tích, vị trí)
- 🎬 **YouTube, TikTok, Facebook Video** — transcript + metadata
- 📄 **PDF** — text + tables + metadata extraction
- 🐙 **GitHub** — README, code, repo info
- 🌐 **Generic** — bất kỳ URL nào → clean markdown + smart chunks

### Pricing

- **Free**: 100 requests/ngày (đăng ký là dùng được, không cần thẻ)
- **Starter**: $19/tháng — 10,000 req, video parsers, priority support
- **Pro**: $79/tháng — 100,000 req, custom parsers, learning engine
- **Enterprise**: Custom

### Tech Stack

- **Backend**: Python + FastAPI
- **Rendering**: Playwright (async, headless)
- **Database**: Supabase (PostgreSQL)
- **Deploy**: Railway (API) + Vercel (docs)
- **SDKs**: Python (PyPI) + JavaScript (npm)

### Links

- 🌐 Website: [crawlkit.org](https://crawlkit.org)
- 📖 API Docs: [api.crawlkit.org/docs](https://api.crawlkit.org/docs)
- 🐍 Python SDK: `pip install crawlkit`
- 📦 JS SDK: `npm install paparusi-crawlkit`

### Use Cases thực tế

1. **RAG Pipeline** — Crawl docs → chunk → feed vào vector DB → LLM search
2. **Legal AI** — Crawl 60,000+ văn bản pháp luật VN (mình đã dùng cho dự án Legal AI Agent — 100 stars trên GitHub)
3. **Content Monitoring** — Track thay đổi trên website đối thủ
4. **Video Analysis** — Extract transcript YouTube → tóm tắt bằng AI
5. **Data Pipeline** — Batch crawl 100 URLs → structured JSON → database

### Feedback?

Mình đang tìm early adopters để cải thiện sản phẩm. Nếu bạn đang build AI app và cần data từ web, thử CrawlKit và cho mình biết:
- Parser nào bạn cần thêm?
- API response format có OK không?
- Có gì confusing trong docs?

Đăng ký free: [crawlkit.org](https://crawlkit.org) — 100 req/ngày, không cần thẻ tín dụng.

---

*P/S: Mình cũng đang build Legal AI Agent (open source, 100 stars) — dùng CrawlKit để crawl toàn bộ hệ thống pháp luật VN. Nếu quan tâm: [github.com/Paparusi/legal-ai-agent](https://github.com/Paparusi/legal-ai-agent)*

---

## English version (Reddit r/webdev, r/machinelearning, HackerNews)

### Title: I built a crawler API that handles both web pages and video transcripts in one call

Every AI agent needs web data, but getting clean, structured data is painful. JavaScript rendering, anti-bot protection, video content locked in players — and no single tool handles both web AND video.

So I built **CrawlKit** — one API call, auto-detects content type, returns structured data ready for RAG.

**What makes it different:**
- 🎬 **Video crawling** — YouTube, TikTok transcripts in 2-3 seconds. Firecrawl, Crawl4AI, Jina can't do this.
- 🧩 **Smart parsers** — Domain-specific extraction (legal docs, news, real estate, finance)  
- 📦 **RAG-ready chunks** — Auto-split by content structure, with token counts
- 🔄 **Learning engine** — Adapts to website changes automatically

```python
# Web page
resp = httpx.post("https://api.crawlkit.org/v1/scrape", 
    json={"url": "https://example.com/article", "chunk": True},
    headers={"X-API-Key": "ck_xxx"})

# Same API for video — auto-detects
resp = httpx.post("https://api.crawlkit.org/v1/scrape",
    json={"url": "https://youtube.com/watch?v=abc123"})
# Returns: transcript, duration, chapters, RAG chunks
```

**Free tier**: 100 req/day, no credit card needed.

- Website: [crawlkit.org](https://crawlkit.org)
- Python: `pip install crawlkit`
- JS: `npm install paparusi-crawlkit`

Looking for feedback from fellow devs. What parsers would you want? What's your current crawling pain point?
