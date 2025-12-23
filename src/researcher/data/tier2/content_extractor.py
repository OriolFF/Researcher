"""
Advanced content extraction for Tier 2 sources.

Uses trafilatura for clean text extraction and markdownification.
"""

import trafilatura
from markdownify import markdownify as md

from researcher.core.logging import logger


class ContentExtractor:
    """
    Advanced content extraction using trafilatura and markdown conversion.
    """
    
    @staticmethod
    def extract(html: str) -> str:
        """
        Extract clean text formatted as markdown.
        
        Args:
            html: Raw HTML content
            
        Returns:
            Cleaned markdown text
        """
        if not html:
            return ""
            
        try:
            # Trafilatura is excellent for stripping boilerplates
            downloaded = trafilatura.extract(
                html, 
                include_comments=False,
                include_tables=True,
                include_links=True,
                deduplicate=True
            )
            
            if downloaded:
                # Convert to markdown for better LLM parsing
                return md(downloaded)
                
            return ""
        except Exception as e:
            logger.error(f"Trafilatura extraction failed: {e}")
            return ""
            
    @staticmethod
    def get_metadata(html: str) -> dict[str, any]:
        """Extract metadata using trafilatura."""
        if not html:
            return {}
            
        try:
            metadata = trafilatura.extract_metadata(html)
            if metadata:
                return {
                    "author": metadata.author,
                    "date": metadata.date,
                    "title": metadata.title,
                    "publisher": metadata.sitename,
                }
            return {}
        except Exception as e:
            logger.error(f"Metadata extraction failed: {e}")
            return {}
