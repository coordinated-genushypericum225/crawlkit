"""
TikTok Parser — Extract metadata and captions from TikTok videos.

Features:
- Video metadata (title, author, likes, shares, comments)
- Auto-captions when available
- Hashtag extraction
- Sound/music info
- No video download
"""

from __future__ import annotations
import re
import logging
from typing import Any, Optional

from ..base import BaseParser

logger = logging.getLogger(__name__)


class TikTokParser(BaseParser):
    name = "tiktok"
    domain = "tiktok.com"

    URL_PATTERNS = [
        r'(?:https?://)?(?:www\.)?tiktok\.com/@[\w.]+/video/(\d+)',
        r'(?:https?://)?(?:vm\.)?tiktok\.com/(\w+)',
        r'(?:https?://)?(?:www\.)?tiktok\.com/t/(\w+)',
    ]

    def can_handle(self, url: str) -> bool:
        return "tiktok.com" in url

    def parse(self, html: str, url: str = "", text: str = "") -> dict[str, Any]:
        """Parse TikTok video — extract metadata + captions."""
        result = {
            "source": "tiktok",
            "url": url,
        }

        metadata = self._get_metadata(url)
        if metadata:
            result.update(metadata)
        else:
            result["error"] = "Failed to extract TikTok metadata"

        result["content_length"] = len(result.get("description", ""))

        return result

    def _get_metadata(self, url: str) -> Optional[dict]:
        """Extract TikTok video metadata via yt-dlp."""
        try:
            import yt_dlp

            opts = {
                "skip_download": True,
                "quiet": True,
                "no_warnings": True,
            }

            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)

            result = {
                "title": info.get("title", "") or info.get("description", "")[:100],
                "description": info.get("description", ""),
                "duration": info.get("duration", 0),
                "view_count": info.get("view_count", 0),
                "like_count": info.get("like_count", 0),
                "comment_count": info.get("comment_count", 0),
                "share_count": info.get("repost_count", 0),  # Renamed for consistency
                "upload_date": self._format_date(info.get("upload_date", "")),
                "thumbnail": info.get("thumbnail", ""),
                "video_id": info.get("id", ""),
            }
            
            # Creator info
            result["creator"] = {
                "username": info.get("uploader_id", ""),
                "display_name": info.get("uploader", ""),
                "profile_url": info.get("uploader_url", ""),
            }

            # Extract hashtags from description
            description = result["description"]
            hashtags = re.findall(r'#(\w+)', description)
            result["hashtags"] = hashtags

            # Sound/music info
            if info.get("track"):
                result["music"] = {
                    "track": info.get("track", ""),
                    "artist": info.get("artist", ""),
                }

            # Subtitles/captions with segments
            subs = info.get("subtitles", {})
            auto_subs = info.get("automatic_captions", {})

            for lang in ["vi", "en"]:
                for sub_source, is_auto in [(subs, False), (auto_subs, True)]:
                    if lang in sub_source:
                        transcript_data = self._extract_subs_with_segments(sub_source[lang])
                        if transcript_data:
                            result["transcript"] = transcript_data["text"]
                            result["transcript_segments"] = transcript_data["segments"]
                            result["transcript_language"] = lang
                            result["transcript_is_auto"] = is_auto
                            result["content_length"] = len(transcript_data["text"])
                            break
                if "transcript" in result:
                    break

            return result

        except ImportError:
            logger.warning("yt-dlp not installed")
            return None
        except Exception as e:
            logger.error(f"TikTok extraction failed: {e}")
            return None

    def _extract_subs(self, sub_formats: list) -> Optional[str]:
        """Extract subtitle text from yt-dlp subtitle formats."""
        try:
            import httpx

            json3 = [s for s in sub_formats if s.get("ext") == "json3"]
            if not json3:
                return None

            r = httpx.get(json3[0]["url"], timeout=10)
            if r.status_code != 200:
                return None

            data = r.json()
            texts = []
            for event in data.get("events", []):
                for seg in event.get("segs", []):
                    t = seg.get("utf8", "").strip()
                    if t and t != "\n":
                        texts.append(t)

            return " ".join(texts) if texts else None
        except Exception:
            return None
    
    def _extract_subs_with_segments(self, sub_formats: list) -> Optional[dict]:
        """Extract subtitle text with timestamped segments."""
        try:
            import httpx

            json3 = [s for s in sub_formats if s.get("ext") == "json3"]
            if not json3:
                return None

            r = httpx.get(json3[0]["url"], timeout=10)
            if r.status_code != 200:
                return None

            data = r.json()
            texts = []
            segments = []
            
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
                    texts.append(seg_text)
                    segments.append({
                        "start": round(start, 1),
                        "duration": round(duration, 1),
                        "text": seg_text
                    })

            if texts:
                return {
                    "text": " ".join(texts),
                    "segments": segments
                }
            return None
        except Exception:
            return None

    def _format_date(self, date_str: str) -> str:
        if len(date_str) == 8:
            return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        return date_str
