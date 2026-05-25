"""
MemoraAI - Text Cleaner
Clean and normalize text content from various sources.
"""

import re
from typing import Optional
import structlog

logger = structlog.get_logger(__name__)


class TextCleaner:
    """
    Text cleaning and normalization utilities.
    
    Handles:
    - Whitespace normalization
    - Special character removal
    - Encoding cleanup
    - HTML entity decoding
    - Formatting standardization
    """

    def __init__(self):
        self._html_entity_map = {
            "&amp;": "&",
            "&lt;": "<",
            "&gt;": ">",
            "&quot;": '"',
            "&apos;": "'",
            "&#39;": "'",
            "&nbsp;": " ",
            "&mdash;": "—",
            "&ndash;": "–",
            "&hellip;": "...",
            "&copy;": "©",
            "&reg;": "®",
            "&trade;": "™",
        }

    def clean(self, text: str, options: Optional[dict] = None) -> str:
        """
        Clean and normalize text.
        
        Args:
            text: Text to clean
            options: Cleaning options dict
            
        Returns:
            Cleaned text
        """
        options = options or {}

        text = self._decode_html_entities(text)
        text = self._remove_control_characters(text)
        text = self._normalize_unicode(text)
        text = self._normalize_whitespace(text)
        
        if options.get("remove_urls", False):
            text = self._remove_urls(text)
        
        if options.get("remove_emails", False):
            text = self._remove_emails(text)
            
        if options.get("remove_phone_numbers", False):
            text = self._remove_phone_numbers(text)
            
        text = self._normalize_punctuation(text)
        text = self._fix_common_issues(text)
        text = text.strip()

        logger.debug("text_cleaned", original_length=len(text), cleaned_length=len(text))
        return text

    def _decode_html_entities(self, text: str) -> str:
        """Decode HTML entities."""
        for entity, char in self._html_entity_map.items():
            text = text.replace(entity, char)
        
        def replace_numeric(match):
            try:
                return chr(int(match.group(1)))
            except (ValueError, OverflowError):
                return match.group(0)
        
        text = re.sub(r"&#(\d+);", replace_numeric, text)
        text = re.sub(r"&#x([0-9a-fA-F]+);", lambda m: chr(int(m.group(1), 16)), text)
        
        return text

    def _remove_control_characters(self, text: str) -> str:
        """Remove control characters but preserve newlines."""
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
        return text

    def _normalize_unicode(self, text: str) -> str:
        """Normalize unicode characters."""
        import unicodedata
        text = unicodedata.normalize("NFKC", text)
        return text

    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace patterns."""
        text = re.sub(r"\r\n|\r", "\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" ?\n ?", "\n", text)
        text = re.sub(r"^\s+$", "", text, flags=re.MULTILINE)
        return text

    def _remove_urls(self, text: str) -> str:
        """Remove URLs from text."""
        url_pattern = r"https?://\S+"
        text = re.sub(url_pattern, "", text)
        return text

    def _remove_emails(self, text: str) -> str:
        """Remove email addresses from text."""
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        text = re.sub(email_pattern, "", text)
        return text

    def _remove_phone_numbers(self, text: str) -> str:
        """Remove phone numbers from text."""
        phone_pattern = r"\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"
        text = re.sub(phone_pattern, "", text)
        return text

    def _normalize_punctuation(self, text: str) -> str:
        """Normalize punctuation marks."""
        text = re.sub(r"\.{3,}", "...", text)
        text = re.sub(r"[^a-zA-Z0-9\s.,!?;:'\"()\[\]{}-—–]", "", text)
        return text

    def _fix_common_issues(self, text: str) -> str:
        """Fix common text issues."""
        text = re.sub(r"([a-z])\.([A-Z])", r"\1. \2", text)
        text = re.sub(r"([a-z]),([a-zA-Z])", r"\1, \2", text)
        text = re.sub(r"([a-z])\(([a-zA-Z])", r"\1 (\2", text)
        text = re.sub(r"([a-z])\)([a-zA-Z])", r"\1) \2", text)
        return text

    def split_sentences(self, text: str) -> list[str]:
        """Split text into sentences."""
        sentence_endings = r"[.!?]+[\s\n]+"
        sentences = re.split(sentence_endings, text)
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences

    def truncate(self, text: str, max_length: int, suffix: str = "...") -> str:
        """Truncate text to maximum length."""
        if len(text) <= max_length:
            return text
        
        truncated = text[: max_length - len(suffix)].rsplit(" ", 1)[0]
        return truncated + suffix


class ContentFilter:
    """Filter content based on quality and relevance criteria."""

    MIN_CONTENT_LENGTH = 50
    MAX_CONTENT_LENGTH = 1_000_000

    def is_valid(self, text: str) -> bool:
        """Check if content meets quality criteria."""
        if len(text) < self.MIN_CONTENT_LENGTH:
            logger.debug("content_too_short", length=len(text))
            return False
        
        if len(text) > self.MAX_CONTENT_LENGTH:
            logger.debug("content_too_long", length=len(text))
            return False
        
        alpha_ratio = sum(c.isalpha() for c in text) / max(len(text), 1)
        if alpha_ratio < 0.3:
            logger.debug("content_low_alpha_ratio", ratio=alpha_ratio)
            return False
        
        return True

    def extract_key_phrases(self, text: str, max_phrases: int = 10) -> list[str]:
        """Extract key phrases from text."""
        words = re.findall(r"\b[A-Z][a-z]+\b", text)
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        sorted_phrases = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [phrase for phrase, _ in sorted_phrases[:max_phrases]]


text_cleaner = TextCleaner()
content_filter = ContentFilter()