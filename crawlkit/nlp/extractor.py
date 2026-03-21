"""
NLP Extraction Module — Vietnamese and English support.

Features:
- Vietnamese entity extraction (people, organizations, locations, dates)
- Keyword extraction (TF-IDF or RAKE)
- Language detection
"""

from __future__ import annotations
import re
from typing import Optional
from collections import Counter


class NLPExtractor:
    """Extract entities and keywords from text."""
    
    def __init__(self):
        self._ner_model = None
        self._tfidf_vectorizer = None
        self._rake = None
    
    def extract(self, text: str, lang: Optional[str] = None) -> dict:
        """
        Extract entities and keywords from text.
        
        Args:
            text: Input text
            lang: Language code ('vi' or 'en'), auto-detect if None
        
        Returns:
            Dict with entities, keywords, and detected language
        """
        if not text or len(text.strip()) < 10:
            return {"entities": [], "keywords": [], "language": "unknown"}
        
        # Detect language if not provided
        if not lang:
            lang = self.detect_language(text)
        
        # Extract entities
        entities = self.extract_entities(text, lang)
        
        # Extract keywords
        keywords = self.extract_keywords(text, lang)
        
        return {
            "entities": entities,
            "keywords": keywords,
            "language": lang
        }
    
    def detect_language(self, text: str) -> str:
        """
        Detect language (Vietnamese vs English).
        
        Args:
            text: Input text
        
        Returns:
            'vi' or 'en'
        """
        try:
            from langdetect import detect
            detected = detect(text[:1000])  # Check first 1000 chars
            return detected if detected in ["vi", "en"] else "en"
        except:
            # Fallback: check for Vietnamese characters
            vietnamese_chars = re.findall(r'[ăâđêôơưàảãáạằẳẵắặầẩẫấậèẻẽéẹềểễếệìỉĩíịòỏõóọồổỗốộờởỡớợùủũúụừửữứựỳỷỹýỵ]', text.lower())
            ratio = len(vietnamese_chars) / max(len(text), 1)
            return "vi" if ratio > 0.05 else "en"
    
    def extract_entities(self, text: str, lang: str) -> list[dict]:
        """
        Extract named entities (people, organizations, locations, dates).
        
        Args:
            text: Input text
            lang: Language code
        
        Returns:
            List of entity dicts with type and text
        """
        entities = []
        
        if lang == "vi":
            entities.extend(self._extract_vietnamese_entities(text))
        else:
            entities.extend(self._extract_english_entities(text))
        
        return entities
    
    def _extract_vietnamese_entities(self, text: str) -> list[dict]:
        """Extract Vietnamese entities using underthesea."""
        entities = []
        
        try:
            from underthesea import ner
            
            # Run NER
            ner_results = ner(text)
            
            # Parse results
            current_entity = []
            current_type = None
            
            for word, tag in ner_results:
                if tag.startswith('B-'):
                    # Begin new entity
                    if current_entity:
                        entities.append({
                            "text": " ".join(current_entity),
                            "type": current_type
                        })
                    current_entity = [word]
                    current_type = tag[2:].lower()  # Remove B- prefix
                elif tag.startswith('I-') and current_entity:
                    # Inside entity
                    current_entity.append(word)
                else:
                    # Outside entity
                    if current_entity:
                        entities.append({
                            "text": " ".join(current_entity),
                            "type": current_type
                        })
                        current_entity = []
                        current_type = None
            
            # Add last entity if exists
            if current_entity:
                entities.append({
                    "text": " ".join(current_entity),
                    "type": current_type
                })
        
        except ImportError:
            # Fallback: regex-based extraction for Vietnamese
            entities.extend(self._extract_vietnamese_regex(text))
        except Exception as e:
            print(f"⚠️ Vietnamese NER failed: {e}, using regex fallback")
            entities.extend(self._extract_vietnamese_regex(text))
        
        return entities
    
    def _extract_vietnamese_regex(self, text: str) -> list[dict]:
        """Fallback regex-based Vietnamese entity extraction."""
        entities = []
        
        # Dates (dd/mm/yyyy, dd-mm-yyyy)
        date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b'
        for match in re.finditer(date_pattern, text):
            entities.append({"text": match.group(), "type": "date"})
        
        # Vietnamese dates (ngày ... tháng ... năm ...)
        vn_date_pattern = r'ngày\s+\d{1,2}\s+tháng\s+\d{1,2}\s+năm\s+\d{4}'
        for match in re.finditer(vn_date_pattern, text, re.IGNORECASE):
            entities.append({"text": match.group(), "type": "date"})
        
        # Titles/Organizations (contains capital words)
        org_pattern = r'\b(?:[A-ZÀÁẢÃẠĂẰẮẴẶẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴ][a-zàáảãạăằắẵặầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵ]+\s*){2,}'
        for match in re.finditer(org_pattern, text):
            phrase = match.group().strip()
            if len(phrase.split()) >= 2:  # At least 2 words
                entities.append({"text": phrase, "type": "organization"})
        
        return entities
    
    def _extract_english_entities(self, text: str) -> list[dict]:
        """Extract English entities using simple patterns."""
        entities = []
        
        # Dates (various formats)
        date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b',
            r'\b\d{4}-\d{2}-\d{2}\b',
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b'
        ]
        for pattern in date_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entities.append({"text": match.group(), "type": "date"})
        
        # Capitalized phrases (potential names/orgs)
        cap_pattern = r'\b(?:[A-Z][a-z]+\s*){2,}'
        for match in re.finditer(cap_pattern, text):
            phrase = match.group().strip()
            if len(phrase.split()) >= 2:
                entities.append({"text": phrase, "type": "person"})
        
        return entities
    
    def extract_keywords(self, text: str, lang: str, top_n: int = 10) -> list[str]:
        """
        Extract top keywords using TF-IDF or RAKE.
        
        Args:
            text: Input text
            lang: Language code
            top_n: Number of keywords to return
        
        Returns:
            List of keyword strings
        """
        if len(text.split()) < 20:
            # Text too short for meaningful keyword extraction
            return []
        
        try:
            # Try RAKE first (works for both languages)
            return self._extract_keywords_rake(text, lang, top_n)
        except:
            # Fallback to simple frequency-based extraction
            return self._extract_keywords_frequency(text, top_n)
    
    def _extract_keywords_rake(self, text: str, lang: str, top_n: int) -> list[str]:
        """Extract keywords using RAKE algorithm."""
        try:
            from rake_nltk import Rake
            
            # Initialize RAKE
            if lang == "vi":
                # For Vietnamese, use no stopwords (RAKE doesn't support it well)
                rake = Rake(language='english', max_length=3)
            else:
                rake = Rake(language='english', max_length=3)
            
            rake.extract_keywords_from_text(text)
            keywords = rake.get_ranked_phrases()
            
            # Return top N
            return keywords[:top_n]
        
        except Exception as e:
            print(f"⚠️ RAKE extraction failed: {e}")
            return self._extract_keywords_frequency(text, top_n)
    
    def _extract_keywords_frequency(self, text: str, top_n: int) -> list[str]:
        """Fallback: extract keywords by frequency."""
        # Tokenize
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Remove short words and common stopwords
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                    'của', 'và', 'các', 'có', 'được', 'từ', 'trong', 'cho', 'với', 'là',
                    'này', 'đã', 'sẽ', 'theo', 'về', 'tại', 'người', 'việc', 'không'}
        
        filtered = [w for w in words if len(w) > 3 and w not in stopwords]
        
        # Count frequencies
        counter = Counter(filtered)
        
        # Return top N
        return [word for word, count in counter.most_common(top_n)]


# Global singleton
_extractor = None

def get_extractor() -> NLPExtractor:
    """Get or create global NLP extractor."""
    global _extractor
    if _extractor is None:
        _extractor = NLPExtractor()
    return _extractor
