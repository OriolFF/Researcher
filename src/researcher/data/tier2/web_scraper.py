"""
Custom web scraper for Tier 2 content extraction.

Uses BeautifulSoup and Selectolax for high-performance extraction of main content from historical sources.
"""

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from researcher.core.logging import logger


class WebScraper:
    """
    Custom scraper for extracting detailed content from historical web sources.
    """
    
    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
    
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=2, max=5),
        reraise=True
    )
    async def fetch_html(self, url: str) -> str | None:
        """Fetch raw HTML from a URL."""
        try:
            logger.debug(f"Fetching HTML from: {url}")
            async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.text
        except Exception as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            return None
            
    def extract_main_content(self, html: str) -> str:
        """
        Extract main article content using basic heuristics.
        
        Focuses on text within <article>, <main>, and <p> tags.
        """
        if not html:
            return ""
            
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove noisy elements
        for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script.decompose()
            
        # Try to find main article container
        main_content = soup.find('article') or soup.find('main') or soup.find('div', class_='content')
        
        if main_content:
            text = main_content.get_text(separator='\n')
        else:
            # Fallback to all paragraphs
            paragraphs = soup.find_all('p')
            text = '\n'.join([p.get_text() for p in paragraphs])
            
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        return '\n'.join(chunk for chunk in chunks if chunk)
        
    def extract_metadata(self, html: str) -> dict[str, str]:
        """Extract metadata like author, publish date, and title."""
        if not html:
            return {}
            
        soup = BeautifulSoup(html, 'html.parser')
        metadata = {}
        
        # Title
        metadata['title'] = soup.title.string if soup.title else ""
        
        # Open Graph and meta tags
        meta_mapping = {
            "author": ["author", "article:author", "og:author"],
            "date": ["article:published_time", "pubdate", "date"],
            "publisher": ["og:site_name", "publisher"]
        }
        
        for key, selectors in meta_mapping.items():
            for selector in selectors:
                tag = soup.find("meta", property=selector) or soup.find("meta", attrs={"name": selector})
                if tag and tag.get("content"):
                    metadata[key] = tag.get("content")
                    break
                    
        return metadata
