"""
Custom tools for the PydanticAI agent.

Includes DuckDuckGo search for free Tier 1 research and verification tools.
"""

from duckduckgo_search import DDGS
from researcher.core.logging import logger
from researcher.domain.models import Source, ResearchTier

async def ddg_search(query: str, max_results: int = 5) -> list[dict]:
    """
    Perform a free web search using DuckDuckGo.
    
    Args:
        query: Search query
        max_results: Max results to return
        
    Returns:
        List of dicts with 'title', 'href', and 'body'
    """
    try:
        logger.info(f"Performing DuckDuckGo search for: {query}")
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            return results
    except Exception as e:
        logger.error(f"DuckDuckGo search failed: {e}")
        return []

def format_ddg_as_sources(results: list[dict]) -> list[Source]:
    """Convert DuckDuckGo results to domain Source models."""
    sources = []
    for res in results:
        sources.append(Source(
            url=res.get('href', ''),
            title=res.get('title', 'Unknown'),
            tier=ResearchTier.TIER1,
            credibility_score=0.6 # Default for web search
        ))
    return sources
