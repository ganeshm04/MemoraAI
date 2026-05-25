"""
MemoraAI - PDF Parser
Extract text content from PDF documents.
"""

from typing import Optional
from pathlib import Path
import structlog

logger = structlog.get_logger(__name__)


class PDFParser:
    """
    PDF text extraction with multiple backend support.
    
    Supports:
    - pdfplumber (primary)
    - PyMuPDF (fallback)
    - PyPDF2 (last resort)
    """

    def __init__(self):
        self.encoding = "utf-8"

    async def extract_text(self, file_path: str) -> str:
        """
        Extract text from PDF file.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text content
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        if path.suffix.lower() != ".pdf":
            raise ValueError(f"Not a PDF file: {file_path}")

        file_size = path.stat().st_size
        if file_size > 50 * 1024 * 1024:
            raise ValueError(f"PDF file too large: {file_size / 1024 / 1024:.1f}MB (max: 50MB)")

        logger.info("pdf_extraction_started", file=str(path), size_mb=file_size / 1024 / 1024)

        try:
            text = await self._extract_pdfplumber(path)
        except Exception as e:
            logger.warning("pdfplumber_failed", error=str(e))
            try:
                text = await self._extract_pymupdf(path)
            except Exception as e2:
                logger.warning("pymupdf_failed", error=str(e2))
                text = await self._extract_pypdf2(path)

        text = self._clean_text(text)
        
        logger.info(
            "pdf_extraction_completed",
            file=str(path),
            text_length=len(text),
            pages=self._estimate_pages(text),
        )
        
        return text

    async def _extract_pdfplumber(self, path: Path) -> str:
        """Extract using pdfplumber."""
        import pdfplumber
        
        text_parts = []
        with pdfplumber.open(path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
                    logger.debug("page_extracted", page=page_num, chars=len(page_text))

        return "\n\n".join(text_parts)

    async def _extract_pymupdf(self, path: Path) -> str:
        """Extract using PyMuPDF."""
        import fitz
        
        text_parts = []
        doc = fitz.open(path)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text()
            if page_text:
                text_parts.append(page_text)
                logger.debug("page_extracted", page=page_num + 1, chars=len(page_text))
        
        doc.close()
        return "\n\n".join(text_parts)

    async def _extract_pypdf2(self, path: Path) -> str:
        """Extract using PyPDF2 as last resort."""
        from PyPDF2 import PdfReader
        
        text_parts = []
        reader = PdfReader(path)
        
        for page_num, page in enumerate(reader.pages, 1):
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
                logger.debug("page_extracted", page=page_num, chars=len(page_text))

        return "\n\n".join(text_parts)

    def _clean_text(self, text: str) -> str:
        """Clean extracted PDF text."""
        import re
        
        text = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f]", "", text)
        text = re.sub(r"([a-z])\n([a-z])", r"\1 \2", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" {2,}", " ", text)
        text = text.strip()
        
        return text

    def _estimate_pages(self, text: str) -> int:
        """Estimate number of pages from text length."""
        avg_chars_per_page = 3000
        return max(1, len(text) // avg_chars_per_page)


class PDFValidator:
    """Validate PDF files before processing."""

    ALLOWED_MIME_TYPES = ["application/pdf"]
    MAX_FILE_SIZE = 50 * 1024 * 1024

    def validate(self, file_path: str, mime_type: Optional[str] = None) -> list[str]:
        """
        Validate PDF file.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        path = Path(file_path)

        if not path.exists():
            errors.append(f"File not found: {file_path}")
            return errors

        if mime_type and mime_type not in self.ALLOWED_MIME_TYPES:
            errors.append(f"Invalid MIME type: {mime_type} (expected: application/pdf)")

        file_size = path.stat().st_size
        if file_size == 0:
            errors.append("File is empty")
        elif file_size > self.MAX_FILE_SIZE:
            errors.append(f"File too large: {file_size / 1024 / 1024:.1f}MB (max: 50MB)")

        if path.suffix.lower() != ".pdf":
            errors.append(f"Invalid extension: {path.suffix} (expected: .pdf)")

        return errors


pdf_parser = PDFParser()
pdf_validator = PDFValidator()