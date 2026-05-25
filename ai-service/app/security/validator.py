"""
MemoraAI - Validator
Input validation for API requests.
"""

import re
from typing import Optional
from dataclasses import dataclass
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)


class ContentType(Enum):
    """Supported content types."""
    PDF = "pdf"
    URL = "url"
    TEXT = "text"


@dataclass
class ValidationResult:
    """Validation result."""
    valid: bool
    errors: list[str]
    warnings: list[str]


class InputValidator:
    """Validate API input parameters."""

    MAX_TEXT_LENGTH = 1_000_000
    MAX_URL_LENGTH = 2000
    MAX_FILE_SIZE = 50 * 1024 * 1024

    VALID_URL_PATTERNS = re.compile(
        r"^https?://"
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"
        r"localhost|"
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
        r"(?::\d+)?"
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    def validate_text_input(
        self,
        text: str,
        max_length: int = None,
    ) -> ValidationResult:
        """Validate text input."""
        errors = []
        warnings = []

        if not text:
            errors.append("Text is empty")
            return ValidationResult(False, errors, warnings)

        length = len(text)
        max_len = max_length or self.MAX_TEXT_LENGTH

        if length > max_len:
            errors.append(f"Text too long: {length} chars (max: {max_len})")

        if length < 1:
            errors.append("Text too short")

        null_bytes = text.count("\x00")
        if null_bytes > 0:
            errors.append(f"Invalid characters found: {null_bytes}")

        return ValidationResult(len(errors) == 0, errors, warnings)

    def validate_url(self, url: str) -> ValidationResult:
        """Validate URL format."""
        errors = []
        warnings = []

        if not url:
            errors.append("URL is empty")
            return ValidationResult(False, errors, warnings)

        if len(url) > self.MAX_URL_LENGTH:
            errors.append(f"URL too long: {len(url)} chars (max: {self.MAX_URL_LENGTH})")

        if not self.VALID_URL_PATTERNS.match(url):
            errors.append("Invalid URL format")

        blocked_domains = ["facebook.com", "twitter.com", "instagram.com"]
        for domain in blocked_domains:
            if domain in url.lower():
                warnings.append(f"Potentially blocked domain: {domain}")

        return ValidationResult(len(errors) == 0, errors, warnings)

    def validate_file_upload(
        self,
        filename: str,
        file_size: int,
        allowed_extensions: list[str] = None,
        allowed_mime_types: list[str] = None,
    ) -> ValidationResult:
        """Validate file upload."""
        errors = []
        warnings = []

        allowed_extensions = allowed_extensions or [".pdf"]
        allowed_mime_types = allowed_mime_types or ["application/pdf"]

        if not filename:
            errors.append("Filename is empty")
            return ValidationResult(False, errors, warnings)

        ext = "." + filename.split(".")[-1].lower() if "." in filename else ""
        if ext not in allowed_extensions:
            errors.append(f"Invalid file extension: {ext} (allowed: {allowed_extensions})")

        if file_size == 0:
            errors.append("File is empty")
        elif file_size > self.MAX_FILE_SIZE:
            errors.append(f"File too large: {file_size / 1024 / 1024:.1f}MB (max: 50MB)")

        return ValidationResult(len(errors) == 0, errors, warnings)

    def validate_query(self, query: str) -> ValidationResult:
        """Validate search query."""
        errors = []
        warnings = []

        if not query or not query.strip():
            errors.append("Query is empty")
            return ValidationResult(False, errors, warnings)

        if len(query) > 1000:
            errors.append(f"Query too long: {len(query)} chars (max: 1000)")

        injection_patterns = [
            r"<\|\w+\|>",
            r"\x00",
            r"\x01",
        ]
        for pattern in injection_patterns:
            if re.search(pattern, query):
                errors.append("Invalid characters in query")

        return ValidationResult(len(errors) == 0, errors, warnings)


class ChunkingValidator:
    """Validate chunking configuration."""

    MIN_CHUNK_SIZE = 100
    MAX_CHUNK_SIZE = 2000
    MIN_OVERLAP = 0
    MAX_OVERLAP = 500

    def validate_config(
        self,
        chunk_size: int,
        chunk_overlap: int,
    ) -> ValidationResult:
        """Validate chunking configuration."""
        errors = []

        if chunk_size < self.MIN_CHUNK_SIZE:
            errors.append(f"Chunk size too small: {chunk_size} (min: {self.MIN_CHUNK_SIZE})")
        if chunk_size > self.MAX_CHUNK_SIZE:
            errors.append(f"Chunk size too large: {chunk_size} (max: {self.MAX_CHUNK_SIZE})")

        if chunk_overlap < self.MIN_OVERLAP:
            errors.append(f"Overlap too small: {chunk_overlap} (min: {self.MIN_OVERLAP})")
        if chunk_overlap > self.MAX_OVERLAP:
            errors.append(f"Overlap too large: {chunk_overlap} (max: {self.MAX_OVERLAP})")

        if chunk_overlap >= chunk_size:
            errors.append(f"Overlap ({chunk_overlap}) must be less than chunk size ({chunk_size})")

        return ValidationResult(len(errors) == 0, errors, [])


validator = InputValidator()
chunking_validator = ChunkingValidator()