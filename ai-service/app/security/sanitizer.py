"""
MemoraAI - Sanitizer
Prompt injection defense and content sanitization.
"""

import re
from typing import Optional
from dataclasses import dataclass
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class SanitizationResult:
    """Result of sanitization."""
    safe: bool
    cleaned_text: str
    threats_removed: list[str]
    warnings: list[str]


class ContentSanitizer:
    """
    Content sanitization for prompt injection defense.
    
    Handles:
    - Instruction-like pattern removal
    - Hidden content detection
    - Malicious prompt detection
    - Encoding attack prevention
    """

    INSTRUCTION_PATTERNS = [
        r"(?i)(ignore (previous|above|all)|disregard (previous|above|all))",
        r"(?i)(forget (your|this)|you (must|should|have to))",
        r"(?i)(new (instruction|command|rule))",
        r"(?i)(system:|assistant:|user:|human:)",
        r"(?i)(<\|(?:system|user|assistant)\|>)",
        r"(?i)(\[INST\]|\[\/INST\])",
        r"(?i)(<<SYS>>|<<\/SYS>>)",
        r"(?i)(You are (now a|acting as a|just a))",
        r"(?i)(Now (pretend|act|be|you are))",
        r"(?i)(Override (your|this)|bypass (your|this))",
        r"(?i)(DAN|do anything now|jailbreak)",
    ]

    DANGEROUS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"eval\s*\(",
        r"exec\s*\(",
    ]

    def __init__(self):
        self.instruction_regex = re.compile(
            "|".join(self.INSTRUCTION_PATTERNS),
            re.IGNORECASE | re.DOTALL
        )
        self.dangerous_regex = re.compile(
            "|".join(self.DANGEROUS_PATTERNS),
            re.IGNORECASE | re.DOTALL
        )

    def sanitize(self, text: str) -> SanitizationResult:
        """
        Sanitize text content.
        
        Args:
            text: Text to sanitize
            
        Returns:
            SanitizationResult with cleaned text
        """
        threats_removed = []
        warnings = []
        cleaned = text

        matches = self.instruction_regex.findall(cleaned)
        if matches:
            threats_removed.append(f"instruction_patterns: {len(matches)}")
            cleaned = self.instruction_regex.sub(" ", cleaned)

        matches = self.dangerous_regex.findall(cleaned)
        if matches:
            threats_removed.append(f"dangerous_patterns: {len(matches)}")
            cleaned = self.dangerous_regex.sub(" ", cleaned)

        if self._has_hidden_content(cleaned):
            warnings.append("hidden_content_detected")
            cleaned = self._remove_hidden_content(cleaned)

        cleaned = self._normalize_whitespace(cleaned)

        safe = len(threats_removed) == 0 and len(warnings) == 0

        logger.info(
            "sanitization_completed",
            safe=safe,
            threats_removed=len(threats_removed),
            warnings=len(warnings),
        )

        return SanitizationResult(
            safe=safe,
            cleaned_text=cleaned,
            threats_removed=threats_removed,
            warnings=warnings,
        )

    def _has_hidden_content(self, text: str) -> bool:
        """Check for hidden content patterns."""
        hidden_patterns = [
            r"\x00",
            r"\u200b",
            r"\u202e",
            r"[\x01-\x08]",
        ]
        for pattern in hidden_patterns:
            if re.search(pattern, text):
                return True
        return False

    def _remove_hidden_content(self, text: str) -> str:
        """Remove hidden content."""
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
        text = text.replace("\u200b", "")
        text = text.replace("\u202e", "")
        return text

    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace."""
        text = re.sub(r"\s+", " ", text)
        text = text.strip()
        return text

    def sanitize_query(self, query: str) -> str:
        """
        Sanitize user query.
        
        Args:
            query: User query string
            
        Returns:
            Sanitized query
        """
        result = self.sanitize(query)
        return result.cleaned_text

    def sanitize_context(self, context: list[dict]) -> list[dict]:
        """
        Sanitize retrieved context chunks.
        
        Args:
            context: List of context dicts with 'content' key
            
        Returns:
            Sanitized context
        """
        sanitized = []
        for chunk in context:
            result = self.sanitize(chunk.get("content", ""))
            sanitized.append({
                **chunk,
                "content": result.cleaned_text,
                "_sanitization_warnings": result.warnings,
            })
        return sanitized


class PromptValidator:
    """Validate prompts for injection attempts."""

    MAX_LENGTH = 10000
    MIN_LENGTH = 1

    def validate(self, prompt: str) -> tuple[bool, list[str]]:
        """
        Validate prompt.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        length = len(prompt)
        if length < self.MIN_LENGTH:
            errors.append(f"Prompt too short (min: {self.MIN_LENGTH})")
        if length > self.MAX_LENGTH:
            errors.append(f"Prompt too long (max: {self.MAX_LENGTH})")

        if re.search(r"<\|\w+\|>", prompt):
            errors.append("Potential prompt injection detected")

        null_bytes = prompt.count("\x00")
        if null_bytes > 0:
            errors.append(f"Invalid characters found: {null_bytes}")

        return len(errors) == 0, errors


sanitizer = ContentSanitizer()
prompt_validator = PromptValidator()