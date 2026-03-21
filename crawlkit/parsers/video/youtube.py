"""
YouTube Parser — Extract metadata, transcripts, and chapters from YouTube videos.

Features:
- Video metadata (title, description, duration, views, tags, chapters)
- Auto-caption extraction (Vietnamese + any language)
- Transcript cleanup and structuring
- Timestamp-aligned text segments
- Channel metadata
- No video download — only metadata + text
"""

from __future__ import annotations
import re
import logging
from typing import Any, Optional

from ..base import BaseParser

logger = logging.getLogger(__name__)


class YouTubeParser(BaseParser):
    name = "youtube"
    domain = "youtube.com"

    # Patterns to match YouTube URLs
    URL_PATTERNS = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?youtu\.be/([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})',
    ]

    def can_handle(self, url: str) -> bool:
        return any(re.search(p, url) for p in self.URL_PATTERNS)

    def parse(self, html: str, url: str = "", text: str = "", lang: str = None) -> dict[str, Any]:
        """
        Parse YouTube video — extract metadata + transcript.
        
        Args:
            html: Not used for YouTube (uses yt-dlp)
            url: YouTube video URL
            text: Not used
            lang: Preferred subtitle language (e.g., "en", "vi", "auto")
        """
        video_id = self._extract_video_id(url)
        if not video_id:
            return {"error": "Could not extract YouTube video ID", "url": url}

        result = {
            "source": "youtube",
            "url": url,
            "video_id": video_id,
        }

        # Step 1: Get metadata via yt-dlp
        metadata = self._get_metadata(video_id)
        if metadata:
            result.update(metadata)
            # Add aliases for common fields (for consistency with other video parsers)
            result["channel"] = metadata.get("uploader", "N/A")
            result["views"] = metadata.get("view_count", 0)
            
            # Parse chapters from description if not provided by yt-dlp
            if not metadata.get("chapters") and metadata.get("description"):
                parsed_chapters = self._parse_chapters_from_description(metadata["description"])
                if parsed_chapters:
                    result["chapters"] = parsed_chapters

        # Step 2: Get transcript with language preference
        languages = [lang] if lang else ["vi", "en"]
        transcript = self._get_transcript(video_id, languages=languages)
        if transcript:
            result["transcript"] = transcript["text"]
            result["transcript_segments"] = transcript["segments"]
            result["transcript_language"] = transcript["language"]
            result["transcript_is_auto"] = transcript["is_auto"]
            result["content_length"] = len(transcript["text"])
        else:
            result["transcript"] = ""
            result["transcript_segments"] = []
            result["content_length"] = len(result.get("description", ""))

        return result

    def _extract_video_id(self, url: str) -> Optional[str]:
        for pattern in self.URL_PATTERNS:
            m = re.search(pattern, url)
            if m:
                return m.group(1)
        return None

    def _get_metadata(self, video_id: str) -> Optional[dict]:
        """Extract video metadata via yt-dlp, with oembed fallback."""
        try:
            import yt_dlp

            opts = {
                "skip_download": True,
                "quiet": True,
                "no_warnings": True,
                "extract_flat": False,
                "http_headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                },
            }

            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(
                    f"https://youtube.com/watch?v={video_id}", download=False
                )

            result = {
                "title": info.get("title", ""),
                "description": info.get("description", ""),
                "duration": info.get("duration", 0),
                "view_count": info.get("view_count", 0),
                "like_count": info.get("like_count", 0),
                "comment_count": info.get("comment_count", 0),
                "upload_date": self._format_date(info.get("upload_date", "")),
                "uploader": info.get("uploader", ""),
                "uploader_id": info.get("uploader_id", ""),
                "channel_id": info.get("channel_id", ""),
                "channel_url": info.get("channel_url", ""),
                "categories": info.get("categories", []),
                "tags": info.get("tags", []),
                "thumbnail": info.get("thumbnail", ""),
                "language": info.get("language"),
            }

            # Chapters
            chapters = info.get("chapters") or []
            if chapters:
                result["chapters"] = [
                    {
                        "title": ch.get("title", ""),
                        "start_time": ch.get("start_time", 0),
                        "end_time": ch.get("end_time", 0),
                    }
                    for ch in chapters
                ]

            # Available subtitle languages
            auto_subs = info.get("automatic_captions", {})
            manual_subs = info.get("subtitles", {})
            result["available_languages"] = {
                "manual": list(manual_subs.keys())[:20],
                "auto": [
                    k
                    for k in auto_subs.keys()
                    if not "-" in k  # skip translated variants
                ][:20],
            }

            return result

        except ImportError:
            logger.warning("yt-dlp not installed — trying oembed fallback")
            return self._get_metadata_oembed(video_id)
        except Exception as e:
            logger.error(f"yt-dlp metadata extraction failed: {e} — trying oembed fallback")
            return self._get_metadata_oembed(video_id)

    def _get_metadata_oembed(self, video_id: str) -> Optional[dict]:
        """Extract basic metadata via YouTube oEmbed API (always works, no auth)."""
        try:
            import httpx
            
            url = f"https://www.youtube.com/oembed?url=https://youtube.com/watch?v={video_id}&format=json"
            
            r = httpx.get(url, timeout=10)
            if r.status_code != 200:
                return None
            
            data = r.json()
            
            return {
                "title": data.get("title", ""),
                "uploader": data.get("author_name", ""),
                "thumbnail": data.get("thumbnail_url", ""),
                "description": "",
                "duration": 0,
                "view_count": 0,
                "like_count": 0,
                "comment_count": 0,
                "upload_date": "",
                "uploader_id": "",
                "channel_id": "",
                "channel_url": "",
                "categories": [],
                "tags": [],
                "language": None,
                "available_languages": {"manual": [], "auto": []},
            }
        except Exception as e:
            logger.error(f"oEmbed fallback failed: {e}")
            return None

    def _get_transcript(
        self, video_id: str, languages: list[str] = None
    ) -> Optional[dict]:
        """Extract transcript — try youtube-transcript-api first, fallback to yt-dlp."""
        if languages is None:
            languages = ["vi", "en"]

        # Method 1: youtube-transcript-api (faster, no yt-dlp dependency)
        result = self._transcript_via_api(video_id, languages)
        if result:
            return result

        # Method 2: yt-dlp subtitle extraction (fallback)
        result = self._transcript_via_ytdlp(video_id, languages)
        if result:
            return result

        return None

    def _transcript_via_api(
        self, video_id: str, languages: list[str]
    ) -> Optional[dict]:
        """Extract transcript using youtube-transcript-api."""
        try:
            from youtube_transcript_api import YouTubeTranscriptApi

            # Try each language
            for lang in languages:
                try:
                    # The API returns a list of dicts directly
                    transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])

                    segments = []
                    texts = []
                    for item in transcript_list:
                        seg_text = item.get("text", "").strip()
                        if seg_text and seg_text not in ("[Âm nhạc]", "[âm nhạc]", "[Music]"):
                            segments.append(
                                {
                                    "start": round(item.get("start", 0), 1),
                                    "duration": round(item.get("duration", 0), 1),
                                    "text": seg_text,
                                }
                            )
                            texts.append(seg_text)

                    if texts:
                        full_text = self._clean_transcript(" ".join(texts))
                        return {
                            "text": full_text,
                            "segments": segments,
                            "language": lang,
                            "is_auto": True,  # API doesn't reliably distinguish
                            "method": "youtube-transcript-api",
                        }
                except Exception as e:
                    logger.debug(f"youtube-transcript-api failed for lang {lang}: {e}")
                    continue

            return None

        except ImportError:
            logger.debug("youtube-transcript-api not installed")
            return None
        except Exception as e:
            logger.debug(f"youtube-transcript-api failed: {e}")
            return None

    def _transcript_via_ytdlp(
        self, video_id: str, languages: list[str]
    ) -> Optional[dict]:
        """Extract transcript using yt-dlp subtitle download."""
        try:
            import yt_dlp
            import httpx

            opts = {
                "skip_download": True,
                "writeautomaticsub": True,
                "writesubtitles": True,
                "subtitleslangs": languages,
                "quiet": True,
                "no_warnings": True,
            }

            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(
                    f"https://youtube.com/watch?v={video_id}", download=False
                )

            manual_subs = info.get("subtitles", {})
            auto_subs = info.get("automatic_captions", {})

            # Prefer manual subs, then auto
            for lang in languages:
                for sub_source, is_auto in [
                    (manual_subs, False),
                    (auto_subs, True),
                ]:
                    if lang not in sub_source:
                        continue

                    # Get json3 format
                    json3_subs = [
                        s for s in sub_source[lang] if s.get("ext") == "json3"
                    ]
                    if not json3_subs:
                        continue

                    r = httpx.get(json3_subs[0]["url"], timeout=15)
                    if r.status_code != 200:
                        continue

                    data = r.json()
                    segments = []
                    texts = []

                    for event in data.get("events", []):
                        start = event.get("tStartMs", 0) / 1000
                        duration = event.get("dDurationMs", 0) / 1000
                        seg_texts = []
                        for seg in event.get("segs", []):
                            t = seg.get("utf8", "").strip()
                            if t and t != "\n":
                                seg_texts.append(t)
                        if seg_texts:
                            seg_text = " ".join(seg_texts)
                            if seg_text not in ("[Âm nhạc]", "[âm nhạc]", "[Music]"):
                                segments.append(
                                    {
                                        "start": round(start, 1),
                                        "duration": round(duration, 1),
                                        "text": seg_text,
                                    }
                                )
                                texts.append(seg_text)

                    if texts:
                        full_text = self._clean_transcript(" ".join(texts))
                        return {
                            "text": full_text,
                            "segments": segments,
                            "language": lang,
                            "is_auto": is_auto,
                            "method": "yt-dlp",
                        }

            return None

        except ImportError:
            return None
        except Exception as e:
            logger.debug(f"yt-dlp transcript failed: {e}")
            return None

    def _clean_transcript(self, text: str) -> str:
        """Clean up auto-generated Vietnamese transcript."""
        # Remove duplicate spaces
        text = re.sub(r"\s+", " ", text)
        # Remove [music] tags
        text = re.sub(r"\[(?:âm nhạc|Âm nhạc|Music|music)\]", "", text, flags=re.IGNORECASE)
        # Remove filler sounds
        text = re.sub(r"\b(ừ ừ|ừm|uhm|uh|um)\b", "", text, flags=re.IGNORECASE)
        # Clean up remaining whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _format_date(self, date_str: str) -> str:
        """Convert yt-dlp date format (YYYYMMDD) to ISO."""
        if len(date_str) == 8:
            return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        return date_str
    
    def _parse_chapters_from_description(self, description: str) -> list[dict]:
        """
        Parse chapters from video description timestamps.
        
        Looks for patterns like:
        - 0:00 Intro
        - 2:30 Main Topic
        - 1:15:30 Conclusion
        """
        if not description:
            return []
        
        chapters = []
        # Pattern: timestamp (H:MM:SS or MM:SS or M:SS) followed by title
        pattern = r'(?:^|\n)(?:(\d{1,2}):)?(\d{1,2}):(\d{2})\s+([^\n]+)'
        
        matches = re.finditer(pattern, description, re.MULTILINE)
        for match in matches:
            hours = int(match.group(1)) if match.group(1) else 0
            minutes = int(match.group(2))
            seconds = int(match.group(3))
            title = match.group(4).strip()
            
            # Skip if title is too short or looks like a URL
            if len(title) < 3 or title.startswith('http'):
                continue
            
            start_time = hours * 3600 + minutes * 60 + seconds
            chapters.append({
                "title": title,
                "start_time": start_time,
            })
        
        # Add end_time to each chapter (next chapter's start or video end)
        for i in range(len(chapters)):
            if i < len(chapters) - 1:
                chapters[i]["end_time"] = chapters[i + 1]["start_time"]
            # else: end_time will be set later if we have duration
        
        return chapters if len(chapters) >= 2 else []
