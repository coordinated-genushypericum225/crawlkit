# CrawlKit Python SDK

Official Python SDK for [CrawlKit](https://crawlkit.vercel.app) — Web + Video Intelligence API for AI.

## Installation

```bash
pip install crawlkit
```

## Quick Start

```python
from crawlkit import CrawlKit

# Initialize client
ck = CrawlKit(api_key="ck_free_xxx")

# Scrape a webpage
result = ck.scrape("https://vnexpress.net/thoi-su")
print(result.title)
print(result.content[:200])

# Scrape YouTube video transcript
video = ck.scrape("https://youtu.be/-Td-D-vKJDg")
print(video.content)  # Full transcript

# Batch scrape multiple URLs
results = ck.batch([
    "https://vnexpress.net",
    "https://cafef.vn",
])

for result in results:
    print(f"{result.title}: {len(result.content)} chars")
```

## Async Support

```python
import asyncio
from crawlkit import AsyncCrawlKit

async def main():
    async with AsyncCrawlKit(api_key="ck_free_xxx") as ck:
        result = await ck.scrape("https://example.com")
        print(result.title)

asyncio.run(main())
```

## Features

- 🚀 **Simple & Fast** — Clean API with sync and async support
- 🎥 **Video Intelligence** — Extract transcripts from YouTube videos
- 📄 **Smart Parsing** — Automatic content extraction from any webpage
- 🔄 **Batch Processing** — Scrape multiple URLs efficiently
- 🔗 **Link Discovery** — Find related links on any page
- 💪 **Type Safe** — Full type hints support
- 🛡️ **Error Handling** — Automatic retries and custom exceptions

## API Reference

### `CrawlKit(api_key, base_url=...)`

Main client class.

**Methods:**

#### `scrape(url, chunk=False, chunk_size=1000, parser=None)`
Scrape a single URL.

**Parameters:**
- `url` (str): URL to scrape
- `chunk` (bool): Split content into chunks
- `chunk_size` (int): Size of each chunk
- `parser` (str): Specific parser to use

**Returns:** `ScrapeResult`

#### `batch(urls, chunk=False, chunk_size=1000)`
Scrape multiple URLs in one request.

**Parameters:**
- `urls` (list[str]): List of URLs to scrape
- `chunk` (bool): Split content into chunks
- `chunk_size` (int): Size of each chunk

**Returns:** `list[ScrapeResult]`

#### `discover(url, limit=20)`
Discover links from a page.

**Parameters:**
- `url` (str): URL to discover links from
- `limit` (int): Maximum number of links

**Returns:** `list[str]`

#### `health()`
Check API health status.

**Returns:** `dict`

#### `parsers()`
List available parsers.

**Returns:** `list[ParserInfo]`

#### `usage()`
Get your API usage statistics.

**Returns:** `UsageStats`

## Examples

### Chunked Content

```python
result = ck.scrape(
    "https://en.wikipedia.org/wiki/Python",
    chunk=True,
    chunk_size=500
)

for i, chunk in enumerate(result.chunks):
    print(f"Chunk {i+1}: {chunk[:50]}...")
```

### Error Handling

```python
from crawlkit import CrawlKit, RateLimitError, AuthenticationError

try:
    result = ck.scrape("https://example.com")
except RateLimitError as e:
    print(f"Rate limited! Retry after {e.retry_after}s")
except AuthenticationError:
    print("Invalid API key")
```

### Context Manager

```python
with CrawlKit(api_key="ck_free_xxx") as ck:
    result = ck.scrape("https://example.com")
    # Client automatically closes
```

## Get an API Key

1. Visit [crawlkit.vercel.app](https://crawlkit.vercel.app)
2. Sign up for a free account
3. Get your API key from the dashboard

**Free tier includes:**
- 100 requests/day
- Web scraping
- Video transcripts
- All parsers

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Links

- 🌐 [Website](https://crawlkit.vercel.app)
- 📚 [Documentation](https://crawlkit.vercel.app/docs)
- 🐛 [Issues](https://github.com/crawlkit/crawlkit-python/issues)
- 💬 [Support](mailto:hello@crawlkit.ai)
