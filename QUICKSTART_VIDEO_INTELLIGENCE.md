# Video Intelligence — Quick Start Guide

## 🚀 30-Second Test

```bash
# Test YouTube with intelligence
curl -X POST http://localhost:8080/v1/scrape \
  -H "Authorization: Bearer ck_free_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://youtu.be/-Td-D-vKJDg",
    "intelligence": true,
    "lang": "en"
  }' | jq '.data.structured.intelligence'
```

**Expected output:**
```json
{
  "key_points": ["...", "...", ...],
  "topics": [{"topic": "...", "relevance": 0.xx}],
  "entities": {"numbers": [...], "money": [...], "names": [...]},
  "summary_points": ["...", "...", ...],
  "content_metrics": {
    "word_count": 3748,
    "words_per_minute": 167.3,
    "speaking_pace": "fast",
    ...
  },
  "language": "en",
  "quotes": ["...", "..."]
}
```

## 🧪 Test All Features

### 1. Basic Video Scraping (No Intelligence)

```bash
curl -X POST http://localhost:8080/v1/scrape \
  -H "Authorization: Bearer ck_free_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtu.be/VIDEO_ID"}'
```

**Returns:** Transcript + basic metadata only

### 2. Video Intelligence (Full Analysis)

```bash
curl -X POST http://localhost:8080/v1/scrape \
  -H "Authorization: Bearer ck_free_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://youtu.be/VIDEO_ID",
    "intelligence": true
  }'
```

**Returns:** Transcript + metadata + intelligence analysis

### 3. Custom Language

```bash
curl -X POST http://localhost:8080/v1/scrape \
  -H "Authorization: Bearer ck_free_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://youtu.be/VIDEO_ID",
    "lang": "vi",
    "intelligence": true
  }'
```

**Returns:** Vietnamese transcript + intelligence

### 4. TikTok Video

```bash
curl -X POST http://localhost:8080/v1/scrape \
  -H "Authorization: Bearer ck_free_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.tiktok.com/@username/video/1234567890",
    "intelligence": true
  }'
```

**Returns:** TikTok captions + hashtags + creator info + intelligence

### 5. Facebook Video

```bash
curl -X POST http://localhost:8080/v1/scrape \
  -H "Authorization: Bearer ck_free_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.facebook.com/watch/?v=1234567890",
    "intelligence": true
  }'
```

**Returns:** Facebook video captions + page info + intelligence

## 📊 What to Check

### ✅ Basic Functionality
- [ ] `structured.transcript` — Full text
- [ ] `structured.transcript_segments` — Array of {start, duration, text}
- [ ] `structured.title`, `structured.duration`, `structured.views`

### ✅ Intelligence Analysis
- [ ] `intelligence.key_points` — 5 most important sentences
- [ ] `intelligence.topics` — 10 topics with relevance scores
- [ ] `intelligence.entities` — Numbers, money, dates, names
- [ ] `intelligence.summary_points` — 5-point summary
- [ ] `intelligence.content_metrics.word_count`
- [ ] `intelligence.content_metrics.words_per_minute`
- [ ] `intelligence.content_metrics.speaking_pace`
- [ ] `intelligence.quotes` — Notable statements

### ✅ YouTube Specific
- [ ] `structured.chapters` — Video chapters (if available)
- [ ] `structured.available_languages` — Subtitle languages
- [ ] `structured.tags`, `structured.categories`

### ✅ TikTok Specific
- [ ] `structured.creator` — {username, display_name, profile_url}
- [ ] `structured.hashtags` — Array of hashtags
- [ ] `structured.music` — {track, artist}

### ✅ Performance
- [ ] Response time < 5 seconds (YouTube)
- [ ] Intelligence processing < 500ms (check logs)
- [ ] No errors in video parsing

## 🐛 Troubleshooting

**"No transcript found"**
- Video may not have captions/subtitles
- Try different `lang` parameter (e.g., "en" instead of "vi")
- Check `structured.available_languages` for supported languages

**"Intelligence not present in response"**
- Verify `intelligence: true` in request body
- Check if video has transcript (intelligence requires transcript)

**"Parser not found"**
- Verify URL is from YouTube, TikTok, or Facebook
- Check URL format (e.g., `youtu.be` vs `youtube.com/watch?v=`)

**Slow response time**
- Normal for long videos (>1 hour)
- Intelligence processing is fast (<500ms), transcript download may be slow
- Check your network connection to video platform

## 🔧 Python Client Example

```python
import httpx
import asyncio

async def test_video_intelligence():
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "http://localhost:8080/v1/scrape",
            json={
                "url": "https://youtu.be/VIDEO_ID",
                "intelligence": True,
                "lang": "en"
            },
            headers={"Authorization": "Bearer ck_free_YOUR_KEY"}
        )
        
        data = resp.json()["data"]
        
        # Access transcript
        print("Title:", data["title"])
        print("Transcript length:", len(data["structured"]["transcript"]))
        
        # Access intelligence
        intel = data["structured"]["intelligence"]
        print("\nKey Points:")
        for point in intel["key_points"]:
            print(f"- {point}")
        
        print("\nTop Topics:")
        for topic in intel["topics"][:5]:
            print(f"- {topic['topic']}: {topic['relevance']}")
        
        print("\nMetrics:")
        print(f"Word count: {intel['content_metrics']['word_count']}")
        print(f"WPM: {intel['content_metrics']['words_per_minute']}")
        print(f"Speaking pace: {intel['content_metrics']['speaking_pace']}")

asyncio.run(test_video_intelligence())
```

## 📝 Sample Videos for Testing

**YouTube (Educational):**
- ICT Trading: `https://youtu.be/-Td-D-vKJDg` (22 min, English, chapters)
- TED Talk: `https://youtu.be/8S0FDjFBj8o` (18 min, English, subtitles)

**YouTube (Vietnamese):**
- News: `https://youtu.be/xxx` (Vietnamese captions)

**TikTok:**
- Any public TikTok video with captions

**Facebook:**
- Any public Facebook video with captions

## 🎯 Key Metrics to Monitor

1. **Intelligence Processing Time** — Should be <500ms
2. **Transcript Extraction Success Rate** — >80% for YouTube
3. **Language Detection Accuracy** — Compare with `transcript_language`
4. **Entity Extraction Quality** — Spot-check numbers, dates, names
5. **Topic Relevance** — Verify topics make sense for video content

---

**Need help?** Check `VIDEO_INTELLIGENCE.md` for full documentation.
