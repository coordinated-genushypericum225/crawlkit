# CrawlKit JavaScript SDK

Official JavaScript/Node.js SDK for [CrawlKit](https://crawlkit.vercel.app) — Web + Video Intelligence API for AI.

## Installation

```bash
npm install crawlkit
# or
yarn add crawlkit
# or
pnpm add crawlkit
```

## Quick Start

```javascript
const { CrawlKit } = require('crawlkit');

// Initialize client
const ck = new CrawlKit({ apiKey: 'ck_free_xxx' });

// Scrape a webpage
const result = await ck.scrape('https://vnexpress.net/thoi-su');
console.log(result.title);
console.log(result.content);

// Scrape YouTube video transcript
const video = await ck.scrape('https://youtu.be/-Td-D-vKJDg');
console.log(video.content); // Full transcript

// Batch scrape multiple URLs
const results = await ck.batch([
  'https://vnexpress.net',
  'https://cafef.vn',
]);

results.forEach(r => console.log(`${r.title}: ${r.content.length} chars`));
```

## ESM Support

```javascript
import { CrawlKit } from 'crawlkit';

const ck = new CrawlKit({ apiKey: 'ck_free_xxx' });
const result = await ck.scrape('https://example.com');
```

## Browser Support

Works in modern browsers with native `fetch`:

```html
<script type="module">
  import { CrawlKit } from './node_modules/crawlkit/src/index.js';
  
  const ck = new CrawlKit({ apiKey: 'ck_free_xxx' });
  const result = await ck.scrape('https://example.com');
  console.log(result);
</script>
```

## Features

- 🚀 **Simple & Fast** — Lightweight with zero dependencies (Node 18+)
- 🎥 **Video Intelligence** — Extract transcripts from YouTube videos
- 📄 **Smart Parsing** — Automatic content extraction from any webpage
- 🔄 **Batch Processing** — Scrape multiple URLs efficiently
- 🔗 **Link Discovery** — Find related links on any page
- 💪 **TypeScript** — Full TypeScript support with type definitions
- 🛡️ **Error Handling** — Automatic retries and custom error classes
- 🌐 **Universal** — Works in Node.js and browsers

## API Reference

### `new CrawlKit(options)`

Create a new CrawlKit client.

**Options:**
- `apiKey` (string, required): Your CrawlKit API key
- `baseUrl` (string): API base URL (default: Railway URL)
- `timeout` (number): Request timeout in ms (default: 30000)
- `maxRetries` (number): Max retry attempts (default: 3)

### Methods

#### `scrape(url, options)`
Scrape a single URL.

**Parameters:**
- `url` (string): URL to scrape
- `options` (object):
  - `chunk` (boolean): Split content into chunks
  - `chunkSize` (number): Size of each chunk
  - `parser` (string): Specific parser to use

**Returns:** `Promise<ScrapeResult>`

#### `batch(urls, options)`
Scrape multiple URLs in one request.

**Parameters:**
- `urls` (string[]): Array of URLs to scrape
- `options` (object):
  - `chunk` (boolean): Split content into chunks
  - `chunkSize` (number): Size of each chunk

**Returns:** `Promise<ScrapeResult[]>`

#### `discover(url, options)`
Discover links from a page.

**Parameters:**
- `url` (string): URL to discover links from
- `options` (object):
  - `limit` (number): Max number of links (default: 20)

**Returns:** `Promise<string[]>`

#### `health()`
Check API health status.

**Returns:** `Promise<object>`

#### `parsers()`
List available parsers.

**Returns:** `Promise<ParserInfo[]>`

#### `usage()`
Get your API usage statistics.

**Returns:** `Promise<UsageStats>`

## Examples

### Chunked Content

```javascript
const result = await ck.scrape('https://en.wikipedia.org/wiki/Python', {
  chunk: true,
  chunkSize: 500
});

result.chunks.forEach((chunk, i) => {
  console.log(`Chunk ${i + 1}: ${chunk.slice(0, 50)}...`);
});
```

### Error Handling

```javascript
const { CrawlKit, RateLimitError, AuthenticationError } = require('crawlkit');

try {
  const result = await ck.scrape('https://example.com');
} catch (error) {
  if (error instanceof RateLimitError) {
    console.log(`Rate limited! Retry after ${error.retryAfter}s`);
  } else if (error instanceof AuthenticationError) {
    console.log('Invalid API key');
  } else {
    console.error(error.message);
  }
}
```

### TypeScript

```typescript
import { CrawlKit, ScrapeResult } from 'crawlkit';

const ck = new CrawlKit({ apiKey: 'ck_free_xxx' });

const result: ScrapeResult = await ck.scrape('https://example.com');
console.log(result.title);
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
- 🐛 [Issues](https://github.com/crawlkit/crawlkit-js/issues)
- 💬 [Support](mailto:hello@crawlkit.ai)
