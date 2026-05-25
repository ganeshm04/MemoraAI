"""
MemoraAI - URL Scraper
Extract content from web pages.
"""

import re
from typing import Optional
import structlog

logger = structlog.get_logger(__name__)


class URLScraper:
    """
    Web content extraction with cleanup and filtering.
    
    Features:
    - HTML parsing with BeautifulSoup
    - Content extraction (main body)
    - Link and script removal
    - Text cleanup and normalization
    """

    def __init__(self):
        self._session = None

    async def scrape(self, url: str, timeout: int = 30) -> str:
        """
        Fetch and extract text content from URL.
        
        Args:
            url: URL to scrape
            timeout: Request timeout in seconds
            
        Returns:
            Extracted text content
        """
        if not self._is_valid_url(url):
            raise ValueError(f"Invalid URL format: {url}")

        logger.info("url_scraping_started", url=url)

        try:
            import httpx
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.get(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Accept": "text/html,application/xhtml+xml",
                        "Accept-Language": "en-US,en;q=0.9",
                    },
                )
                response.raise_for_status()

            content_type = response.headers.get("content-type", "")
            if "text/html" not in content_type:
                logger.warning("non_html_content", url=url, content_type=content_type)

            html = response.text
            text = self._extract_text(html, url)

            logger.info(
                "url_scraping_completed",
                url=url,
                text_length=len(text),
            )

            return text

        except Exception as e:
            logger.error("url_scraping_failed", url=url, error=str(e))
            raise

    def _extract_text(self, html: str, base_url: str) -> str:
        """Extract and clean text from HTML."""
        try:
            from bs4 import BeautifulSoup
            
            soup = BeautifulSoup(html, "lxml")

            for script in soup(["script", "style", "noscript", "iframe", "nav", "footer", "header"]):
                script.decompose()

            article = soup.find("article") or soup.find("main") or soup.find("div", class_=re.compile(r"content|article|post|main"))

            if article:
                content = article
            else:
                body = soup.find("body")
                content = body if body else soup

            text = content.get_text(separator="\n", strip=True)
            text = self._clean_text(text)

            return text

        except ImportError:
            logger.warning("beautifulsoup4_not_available_using_regex")
            return self._extract_text_regex(html)

    def _extract_text_regex(self, html: str) -> str:
        """Fallback text extraction using regex."""
        text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r" {2,}", " ", text)
        text = text.strip()
        return text

    def _clean_text(self, text: str) -> str:
        """Clean extracted text."""
        text = re.sub(r"\r\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        text = text.strip()
        return text

    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid."""
        pattern = re.compile(
            r"^https?://"
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"
            r"localhost|"
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
            r"(?::\d+)?"
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )
        return bool(pattern.match(url))

    async def get_metadata(self, url: str) -> dict:
        """Extract metadata from URL."""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url)
                html = response.text

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "lxml")

            metadata = {
                "url": url,
                "title": self._get_meta_content(soup, ["og:title", "twitter:title", "title"]),
                "description": self._get_meta_content(soup, ["og:description", "twitter:description", "description"]),
                "domain": self._extract_domain(url),
            }

            return metadata

        except Exception as e:
            logger.warning("metadata_extraction_failed", url=url, error=str(e))
            return {"url": url, "title": "", "description": "", "domain": self._extract_domain(url)}

    def _get_meta_content(self, soup, names: list[str]) -> str:
        """Get meta content from soup."""
        for name in names:
            tag = soup.find("meta", attrs={"name": name}) or soup.find("meta", attrs={"property": name})
            if tag and tag.get("content"):
                return tag["content"].strip()
        title_tag = soup.find("title")
        if title_tag:
            return title_tag.text.strip()
        return ""

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        match = re.search(r"https?://([^/]+)", url)
        return match.group(1) if match else ""


class URLValidator:
    """Validate URLs before scraping."""

    BLOCKED_DOMAINS = [
        "facebook.com",
        "twitter.com",
        "x.com",
        "instagram.com",
        "linkedin.com",
        "paypal.com",
        "bank",
    ]

    def validate(self, url: str) -> list[str]:
        """Validate URL."""
        errors = []

        scraper = URLScraper()
        if not scraper._is_valid_url(url):
            errors.append(f"Invalid URL format: {url}")
            return errors

        domain = scraper._extract_domain(url)
        for blocked in self.BLOCKED_DOMAINS:
            if blocked in domain.lower():
                errors.append(f"Scraping blocked domain: {domain}")

        return errors


url_scraper = URLScraper()
url_validator = URLValidator()