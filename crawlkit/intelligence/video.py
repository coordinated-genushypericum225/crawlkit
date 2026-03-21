"""
Video Intelligence — AI-free video content analysis.

Extracts key points, topics, entities, quotes, and summary points from video transcripts
using NLP heuristics and rule-based approaches. No heavy ML dependencies.
"""

from __future__ import annotations
import re
from typing import Optional
from collections import Counter


class VideoIntelligence:
    """AI-free video content analysis using NLP heuristics."""
    
    # Transition words that often indicate key points
    TRANSITION_WORDS = {
        'first', 'second', 'third', 'finally', 'conclusion', 'summary',
        'important', 'crucial', 'key', 'main', 'essential', 'critical',
        'remember', 'note', 'however', 'therefore', 'thus', 'consequently',
        'trước tiên', 'thứ hai', 'thứ ba', 'cuối cùng', 'tóm lại', 'kết luận',
        'quan trọng', 'chính', 'cần lưu ý', 'cần nhớ', 'do đó', 'vì vậy'
    }
    
    # Question words
    QUESTION_WORDS = {'what', 'why', 'how', 'when', 'where', 'who', 'which',
                      'gì', 'tại sao', 'như thế nào', 'khi nào', 'ở đâu', 'ai'}
    
    # Strong statement indicators
    STRONG_INDICATORS = {
        'must', 'should', 'always', 'never', 'best', 'worst', 'only',
        'phải', 'nên', 'luôn', 'không bao giờ', 'tốt nhất', 'duy nhất'
    }
    
    @staticmethod
    def extract_key_points(transcript: str, max_points: int = 5) -> list[str]:
        """
        Extract key points from transcript using sentence scoring.
        
        Scores based on:
        - Position (first/last sentences often important)
        - Transition words
        - Sentence length (not too short, not too long)
        - Contains numbers/statistics
        """
        if not transcript or not transcript.strip():
            return []
        
        # Split into sentences
        sentences = VideoIntelligence._split_sentences(transcript)
        if not sentences:
            return []
        
        # Score each sentence
        scored = []
        total = len(sentences)
        
        for idx, sentence in enumerate(sentences):
            score = 0.0
            lower_sent = sentence.lower()
            words = sentence.split()
            
            # Position score (beginning and end are often important)
            if idx < 3:  # First 3 sentences
                score += 2.0
            elif idx >= total - 3:  # Last 3 sentences
                score += 1.5
            
            # Transition words
            for word in VideoIntelligence.TRANSITION_WORDS:
                if word in lower_sent:
                    score += 1.5
                    break
            
            # Strong indicators
            for word in VideoIntelligence.STRONG_INDICATORS:
                if word in lower_sent:
                    score += 1.0
            
            # Contains numbers (often statistical/important)
            if re.search(r'\d+', sentence):
                score += 0.8
            
            # Length score (prefer medium-length sentences)
            word_count = len(words)
            if 10 <= word_count <= 30:
                score += 1.0
            elif word_count < 5:
                score -= 1.0  # Too short, likely not important
            
            # Questions often highlight important points
            if any(qw in lower_sent for qw in VideoIntelligence.QUESTION_WORDS):
                score += 0.5
            
            scored.append((score, sentence.strip()))
        
        # Sort by score and take top N
        scored.sort(reverse=True, key=lambda x: x[0])
        return [sent for score, sent in scored[:max_points] if score > 0]
    
    @staticmethod
    def extract_topics(transcript: str, max_topics: int = 10) -> list[dict]:
        """
        Extract main topics using keyword frequency analysis.
        
        Returns topics with relevance scores based on TF (term frequency).
        """
        if not transcript or not transcript.strip():
            return []
        
        # Tokenize and clean
        words = VideoIntelligence._tokenize(transcript)
        
        # Filter stopwords and short words
        stopwords = VideoIntelligence._get_stopwords()
        filtered = [w for w in words if w not in stopwords and len(w) >= 3]
        
        if not filtered:
            return []
        
        # Count frequencies
        word_counts = Counter(filtered)
        total_words = len(filtered)
        
        # Calculate relevance (normalized frequency)
        topics = []
        for word, count in word_counts.most_common(max_topics):
            relevance = count / total_words
            # Only include words that appear multiple times and have decent relevance
            if count >= 2 and relevance >= 0.005:
                topics.append({
                    "topic": word,
                    "relevance": round(relevance, 3),
                    "count": count
                })
        
        return topics
    
    @staticmethod
    def detect_language(text: str) -> str:
        """
        Detect transcript language using lightweight heuristics.
        Falls back to langdetect if available.
        """
        if not text or not text.strip():
            return "unknown"
        
        # Simple heuristic: count Vietnamese and English indicators
        vi_chars = len(re.findall(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]', text.lower()))
        en_common = sum(1 for word in ['the', 'is', 'and', 'to', 'of', 'in', 'that', 'it', 'for'] 
                       if f' {word} ' in text.lower())
        
        if vi_chars > 10:
            return "vi"
        elif en_common > 5:
            return "en"
        
        # Try langdetect if available
        try:
            from langdetect import detect
            return detect(text[:1000])  # Sample first 1000 chars
        except ImportError:
            return "unknown"
        except Exception:
            return "unknown"
    
    @staticmethod
    def extract_quotes(transcript: str, max_quotes: int = 5) -> list[str]:
        """
        Extract notable quotes/statements.
        
        Looks for:
        - Text in quotation marks
        - Strong declarative statements
        - Sentences with strong indicators
        """
        if not transcript or not transcript.strip():
            return []
        
        quotes = []
        
        # Find quoted text
        quoted = re.findall(r'["""]([^"""]+)["""]', transcript)
        quotes.extend(quoted[:max_quotes])
        
        if len(quotes) >= max_quotes:
            return quotes[:max_quotes]
        
        # Find strong statements
        sentences = VideoIntelligence._split_sentences(transcript)
        for sent in sentences:
            if len(quotes) >= max_quotes:
                break
            
            lower_sent = sent.lower()
            # Check for strong indicators
            if any(ind in lower_sent for ind in VideoIntelligence.STRONG_INDICATORS):
                # Make sure it's not too long
                if 10 <= len(sent.split()) <= 25:
                    quotes.append(sent.strip())
        
        return quotes[:max_quotes]
    
    @staticmethod
    def generate_summary_points(transcript: str, max_points: int = 5) -> list[str]:
        """
        Generate bullet-point summary using extractive summarization.
        
        Similar to extract_key_points but focuses on comprehensive coverage
        rather than just the most important sentences.
        """
        if not transcript or not transcript.strip():
            return []
        
        sentences = VideoIntelligence._split_sentences(transcript)
        if not sentences:
            return []
        
        # For short transcripts, just return key points
        if len(sentences) <= max_points:
            return [s.strip() for s in sentences]
        
        # Divide transcript into sections
        section_size = len(sentences) // max_points
        summary = []
        
        for i in range(max_points):
            start_idx = i * section_size
            end_idx = (i + 1) * section_size if i < max_points - 1 else len(sentences)
            section = sentences[start_idx:end_idx]
            
            if not section:
                continue
            
            # Find most representative sentence in this section
            # Use the first sentence that's not too short
            for sent in section:
                if len(sent.split()) >= 5:
                    summary.append(sent.strip())
                    break
        
        return summary
    
    @staticmethod
    def extract_entities(transcript: str) -> dict:
        """
        Extract named entities using regex patterns.
        
        Extracts:
        - Numbers (integers, decimals, percentages)
        - Money amounts
        - Dates
        - Times
        - Potential names (capitalized words)
        """
        if not transcript or not transcript.strip():
            return {"numbers": [], "money": [], "dates": [], "times": [], "names": []}
        
        entities = {
            "numbers": [],
            "money": [],
            "dates": [],
            "times": [],
            "names": []
        }
        
        # Numbers (including decimals and percentages)
        numbers = re.findall(r'\b\d+(?:\.\d+)?%?|\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b', transcript)
        entities["numbers"] = list(set(numbers))[:20]
        
        # Money (USD, VND, etc.)
        money = re.findall(r'(?:USD?|VND|đ|\$|€|£)\s*[\d,]+(?:\.\d{2})?|[\d,]+(?:\.\d{2})?\s*(?:USD?|VND|đ|dollars?|đồng)', transcript, re.IGNORECASE)
        entities["money"] = list(set(money))[:10]
        
        # Dates (various formats)
        dates = re.findall(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b', transcript, re.IGNORECASE)
        entities["dates"] = list(set(dates))[:10]
        
        # Times
        times = re.findall(r'\b\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?\b', transcript)
        entities["times"] = list(set(times))[:10]
        
        # Potential names (consecutive capitalized words, but filter common words)
        common_words = {'The', 'A', 'An', 'In', 'On', 'At', 'To', 'For', 'Of', 'With', 'By', 'From', 'This', 'That'}
        name_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b'
        potential_names = re.findall(name_pattern, transcript)
        names = [name for name in set(potential_names) if not any(word in common_words for word in name.split())]
        entities["names"] = names[:15]
        
        return entities
    
    @staticmethod
    def calculate_content_metrics(transcript: str, duration: int) -> dict:
        """
        Calculate content density metrics.
        
        Args:
            transcript: Full transcript text
            duration: Video duration in seconds
        
        Returns:
            Dict with word count, WPM, sentence count, etc.
        """
        if not transcript or not transcript.strip():
            return {
                "word_count": 0,
                "words_per_minute": 0,
                "sentence_count": 0,
                "avg_sentence_length": 0,
                "reading_time_minutes": 0,
                "speaking_pace": "unknown"
            }
        
        words = transcript.split()
        word_count = len(words)
        sentences = VideoIntelligence._split_sentences(transcript)
        sentence_count = len(sentences)
        
        # Calculate metrics
        duration_minutes = duration / 60 if duration > 0 else 1
        wpm = round(word_count / duration_minutes, 1) if duration > 0 else 0
        avg_sentence_length = round(word_count / sentence_count, 1) if sentence_count > 0 else 0
        reading_time = round(word_count / 200, 1)  # Average reading speed: 200 wpm
        
        # Classify speaking pace
        if wpm < 100:
            pace = "slow"
        elif wpm < 150:
            pace = "moderate"
        elif wpm < 180:
            pace = "fast"
        else:
            pace = "very_fast"
        
        return {
            "word_count": word_count,
            "words_per_minute": wpm,
            "sentence_count": sentence_count,
            "avg_sentence_length": avg_sentence_length,
            "reading_time_minutes": reading_time,
            "speaking_pace": pace
        }
    
    # ── Helper Methods ──────────────────────────────────────────────
    
    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        """Split text into sentences."""
        # Simple sentence splitter (handles . ! ?)
        text = re.sub(r'\s+', ' ', text.strip())
        # Split on sentence terminators followed by space and capital letter
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-ZĐ])', text)
        return [s.strip() for s in sentences if s.strip() and len(s.split()) >= 3]
    
    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Tokenize text into words (lowercase, alphanumeric)."""
        # Remove special characters, split, lowercase
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        return [w for w in text.split() if w]
    
    @staticmethod
    def _get_stopwords() -> set:
        """Get common stopwords for English and Vietnamese."""
        english = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'should', 'could', 'may', 'might', 'can', 'this', 'that', 'these',
            'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'my', 'your',
            'his', 'her', 'its', 'our', 'their', 'what', 'which', 'who', 'when',
            'where', 'why', 'how', 'all', 'each', 'every', 'both', 'few', 'more',
            'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
            'same', 'so', 'than', 'too', 'very', 'just', 'now'
        }
        
        vietnamese = {
            'và', 'hoặc', 'nhưng', 'nếu', 'thì', 'của', 'có', 'được', 'là', 'ở',
            'cho', 'với', 'từ', 'đến', 'trong', 'ngoài', 'trên', 'dưới', 'này',
            'đó', 'kia', 'những', 'các', 'cái', 'con', 'người', 'tôi', 'bạn',
            'anh', 'chị', 'em', 'chúng', 'ta', 'mình', 'ai', 'gì', 'đâu', 'nào',
            'sao', 'như', 'thế', 'rất', 'lắm', 'quá', 'đã', 'sẽ', 'đang', 'vẫn',
            'còn', 'không', 'chưa', 'cũng', 'mà', 'hay', 'hoặc', 'thì'
        }
        
        return english | vietnamese
