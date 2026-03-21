# Video Intelligence Engine

CrawlKit's Video Intelligence Engine transforms video scraping into comprehensive content analysis. Extract transcripts, detect key moments, analyze topics, and identify entities — all without heavy ML dependencies.

## Features

### 🎬 Enhanced Video Parsers

**YouTube**
- ✅ Timestamped transcript segments
- ✅ Auto-detected chapters (from YouTube or description parsing)
- ✅ Multi-language subtitle support (`lang` parameter)
- ✅ Rich metadata (views, likes, duration, tags, categories)
- ✅ Available subtitle languages

**TikTok**
- ✅ Auto-captions with timestamps
- ✅ Hashtag extraction
- ✅ Music/sound info
- ✅ Engagement metrics (views, likes, shares, comments)
- ✅ Creator profile info

**Facebook Videos**
- ✅ Video captions with timestamps
- ✅ Engagement metrics
- ✅ Creator/page information

### 🧠 Intelligence Analysis (Opt-in)

When `intelligence=true`, CrawlKit analyzes the transcript and extracts:

1. **Key Points** — Most important sentences (scored by position, keywords, transitions)
2. **Topics** — Main subjects discussed (frequency-based analysis)
3. **Entities** — Numbers, money amounts, dates, times, names (regex extraction)
4. **Summary Points** — Bullet-point summary (extractive)
5. **Quotes** — Notable statements and quotations
6. **Content Metrics** — Word count, WPM, speaking pace, reading time

**Performance:** All intelligence processing completes in <500ms for typical transcripts.

## Usage

### Python

```python
from crawlkit.core.crawler import CrawlKit

crawler = CrawlKit()

# Basic video scraping
result = await crawler.scrape("https://youtu.be/VIDEO_ID")
print(result.structured["transcript"])
print(result.structured["transcript_segments"])

# With intelligence analysis
result = await crawler.scrape(
    url="https://youtu.be/VIDEO_ID",
    intelligence=True,  # Enable intelligence
    lang="en"           # Preferred subtitle language
)

# Access intelligence data
intel = result.structured["intelligence"]
print(intel["key_points"])        # Top 5 key points
print(intel["topics"])            # Main topics with relevance scores
print(intel["entities"])          # Extracted numbers, dates, names, etc.
print(intel["summary_points"])    # 5-point summary
print(intel["content_metrics"])   # Word count, WPM, speaking pace
```

### API (FastAPI)

```bash
# Basic scraping
curl -X POST https://api.crawlkit.ai/v1/scrape \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://youtu.be/VIDEO_ID"
  }'

# With intelligence + language preference
curl -X POST https://api.crawlkit.ai/v1/scrape \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://youtu.be/VIDEO_ID",
    "intelligence": true,
    "lang": "en"
  }'
```

### Response Structure

```json
{
  "success": true,
  "data": {
    "title": "Video Title",
    "content": "Full transcript...",
    "format": "text",
    "structured": {
      "source": "youtube",
      "video_id": "...",
      "channel": "Channel Name",
      "views": 12345,
      "duration": 1344,
      "upload_date": "2025-09-30",
      "transcript": "Full transcript text...",
      "transcript_segments": [
        {"start": 0.0, "duration": 5.2, "text": "Welcome..."},
        {"start": 5.2, "duration": 6.9, "text": "Today we discuss..."}
      ],
      "transcript_language": "en",
      "transcript_is_auto": true,
      "chapters": [
        {"title": "Intro", "start_time": 0, "end_time": 150},
        {"title": "Main Topic", "start_time": 150, "end_time": 900}
      ],
      "available_languages": {
        "manual": ["en", "es"],
        "auto": ["en", "vi", "ja", "ko", ...]
      },
      "intelligence": {
        "key_points": [
          "Most important sentence 1...",
          "Most important sentence 2...",
          ...
        ],
        "topics": [
          {"topic": "trading", "relevance": 0.085, "count": 42},
          {"topic": "market", "relevance": 0.052, "count": 26}
        ],
        "entities": {
          "numbers": ["2025", "30", "857"],
          "money": ["$100", "2000 USD"],
          "dates": ["09/30/2025"],
          "times": ["9:30 AM"],
          "names": ["John Smith", "New York"]
        },
        "summary_points": [
          "Summary point 1...",
          "Summary point 2...",
          ...
        ],
        "content_metrics": {
          "word_count": 3748,
          "words_per_minute": 167.3,
          "sentence_count": 263,
          "avg_sentence_length": 14.3,
          "reading_time_minutes": 18.7,
          "speaking_pace": "fast"
        },
        "language": "en",
        "quotes": [
          "Notable quote 1...",
          "Notable quote 2..."
        ]
      }
    }
  }
}
```

## Parameters

### `lang` (optional)
Preferred subtitle language. Examples: `"en"`, `"vi"`, `"es"`, `"ja"`

- For YouTube: requests specific subtitle language or auto-translate
- Falls back to available languages if preferred not found
- Default: tries Vietnamese first, then English

### `intelligence` (optional, default: `false`)
Enable video intelligence analysis.

- `false` (default): Only extract transcript + basic metadata
- `true`: Add full intelligence analysis (key points, topics, entities, etc.)

## Implementation Details

### Lightweight & Fast

- **No heavy ML dependencies** — Uses rule-based NLP heuristics
- **Processing time:** <500ms for typical transcripts
- **Dependencies:** Only `langdetect` (optional, has fallback)
- **Extractive methods:** TextRank-inspired sentence scoring, TF-based topic extraction

### Algorithms

**Key Point Extraction:**
- Scores sentences by position (beginning/end), transition words, strong indicators
- Prefers medium-length sentences with numbers/statistics
- Returns top N highest-scored sentences

**Topic Extraction:**
- Tokenizes and filters stopwords (English + Vietnamese)
- Calculates term frequency with relevance scores
- Returns topics appearing multiple times with >0.5% relevance

**Entity Extraction:**
- Regex patterns for numbers, money, dates, times
- Capitalized word sequences for potential names
- Filters common words to reduce noise

**Content Metrics:**
- WPM = word count / (duration / 60)
- Speaking pace: slow (<100), moderate (100-150), fast (150-180), very fast (>180)
- Reading time based on 200 WPM average

## Use Cases

✅ **AI Chatbots** — Enable video Q&A with extracted transcripts + key points  
✅ **Content Summarization** — Auto-generate video summaries for newsletters/blogs  
✅ **SEO Optimization** — Extract topics and entities for metadata/tags  
✅ **Educational Platforms** — Build searchable video libraries with timestamped content  
✅ **Market Research** — Analyze video content at scale (topics, entities, sentiment)  
✅ **RAG Pipelines** — Chunk video transcripts with metadata for retrieval

## Testing

Run the test suite:

```bash
python3 test_video_intelligence.py
```

This tests:
- Intelligence module functions (key points, topics, entities, etc.)
- YouTube parser integration
- Response structure validation
- Multi-language support

## Roadmap

Future enhancements (not yet implemented):

- [ ] Sentiment analysis (positive/negative/neutral per segment)
- [ ] Speaker diarization (identify multiple speakers)
- [ ] Visual scene detection (integrate with video frames)
- [ ] Auto-generated questions (for Q&A/quizzes)
- [ ] Topic clustering (group related topics)
- [ ] Custom entity types (user-defined patterns)

---

Built with ❤️ for AI-powered video analysis. No OpenAI API required.
