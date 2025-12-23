"""
Advanced Tavily search client for Tier 2 research.

Provides deep search capabilities with academic source filtering and metadata extraction.
"""

from typing import Any

from tavily import TavilyClient as BaseTavilyClient
from tenacity import retry, stop_after_attempt, wait_exponential

from researcher.core.config import settings
from researcher.core.logging import logger
from researcher.domain.models import ResearchTier, Source


class TavilyAdvancedClient:
    """
    Advanced search client using the Tavily API.
    
    Provides deeper research compared to standard web search.
    """
    
    def __init__(self):
        self.api_key = settings.tavily_api_key
        if not self.api_key:
            logger.warning("Tavily API key not found. Tier 2 search will be unavailable.")
            self.client = None
        else:
            self.client = BaseTavilyClient(api_key=self.api_key)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def search(
        self,
        query: str,
        max_results: int = 20,
        search_depth: str = "advanced",
        include_domains: list[str] | None = None,
        exclude_domains: list[str] | None = None,
    ) -> list[Source]:
        """
        Perform an advanced search using Tavily.
        
        Args:
            query: Search query
            max_results: Maximum results to return
            search_depth: "basic" or "advanced"
            include_domains: Specific domains to search
            exclude_domains: Domains to exclude
            
        Returns:
            List of domain Source models
        """
        if not self.client:
            logger.error("Attempted Tier 2 search without Tavily API key")
            return []
            
        try:
            logger.info(f"Performing Tier 2 Tavily search ({search_depth}): {query}")
            
            # Tavily client is synchronous, so we run it in a thread or just use it directly
            # assuming it doesn't block too long for this use case, or we use its async version
            # if available. The tavily-python library has sync methods.
            
            response = self.client.search(
                query=query,
                search_depth=search_depth,
                max_results=max_results,
                include_domains=include_domains,
                exclude_domains=exclude_domains,
                include_answer=False,
                include_raw_content=True,
            )
            
            sources = []
            results = response.get('results', [])
            
            for res in results:
                sources.append(Source(
                    url=res.get('url', ''),
                    title=res.get('title', 'Unknown'),
                    author=res.get('author'),
                    date_published=res.get('published_date'),
                    tier=ResearchTier.TIER2,
                    credibility_score=res.get('score', 0.8)
                ))
                
            return sources
            
        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
            return []
    
    async def get_search_context(self, query: str, max_tokens: int = 4000) -> str:
        """Get compressed search context for the LLM."""
        if not self.client:
            return ""
            
        try:
            return self.client.get_search_context(
                query=query,
                search_depth="advanced",
                max_tokens=max_tokens
            )
        except Exception as e:
            logger.error(f"Tavily context extraction failed: {e}")
            return ""
