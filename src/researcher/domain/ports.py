"""
Domain ports (interfaces/protocols) for the researcher.

Defines abstract interfaces for LLM providers, research providers, and output formatters.
This allows the domain layer to be independent of specific implementations.
"""

from abc import ABC, abstractmethod
from typing import Protocol

from researcher.domain.models import (
    EscalationDecision,
    ResearchQuery,
    ResearchResult,
    Source,
)


class LLMProvider(Protocol):
    """
    Abstract interface for LLM providers.
    
    Implementations handle communication with specific LLM APIs (OpenAI, Anthropic, etc.)
    """
    
    async def complete(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 2000,
    ) -> str:
        """
        Generate a completion from the LLM.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response
        """
        ...
    
    async def complete_structured(
        self,
        messages: list[dict[str, str]],
        response_model: type,
        temperature: float = 0.1,
    ) -> any:
        """
        Generate a structured response matching a Pydantic model.
        
        Args:
            messages: List of message dictionaries
            response_model: Pydantic model class for the response
            temperature: Sampling temperature
            
        Returns:
            Instance of response_model
        """
        ...


class ResearchProvider(Protocol):
    """
    Abstract interface for research providers (Tier 1 or Tier 2).
    
    Implementations handle web search and content extraction.
    """
    
    async def search(
        self,
        query: str,
        max_results: int = 10,
    ) -> list[Source]:
        """
        Search for sources related to the query.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of sources
        """
        ...
    
    async def fetch_content(
        self,
        url: str,
    ) -> str:
        """
        Fetch and extract main content from a URL.
        
        Args:
            url: URL to fetch
            
        Returns:
            Extracted text content
        """
        ...


class EscalationStrategy(Protocol):
    """
    Abstract interface for escalation decision strategies.
    
    Determines when to escalate from Tier 1 to Tier 2.
    """
    
    def should_escalate(
        self,
        tier1_result: ResearchResult,
        query: ResearchQuery,
    ) -> EscalationDecision:
        """
        Determine if escalation to Tier 2 is needed.
        
        Args:
            tier1_result: Result from Tier 1 research
            query: Original research query
            
        Returns:
            Escalation decision with reasoning
        """
        ...


class OutputFormatter(Protocol):
    """
    Abstract interface for output formatters.
    
    Converts research results to different formats (JSON, Markdown, etc.)
    """
    
    def format(self, result: ResearchResult) -> str:
        """
        Format research result.
        
        Args:
            result: Research result to format
            
        Returns:
            Formatted string
        """
        ...


class ResearchRepository(ABC):
    """
    Abstract base class for research result storage.
    
    Implementations handle caching and persistence of research results.
    """
    
    @abstractmethod
    async def save(self, result: ResearchResult) -> str:
        """
        Save a research result.
        
        Args:
            result: Research result to save
            
        Returns:
            Unique identifier for the saved result
        """
        pass
    
    @abstractmethod
    async def get(self, result_id: str) -> ResearchResult | None:
        """
        Retrieve a research result by ID.
        
        Args:
            result_id: Unique identifier
            
        Returns:
            Research result if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def search_by_query(self, query: str) -> list[ResearchResult]:
        """
        Search for cached results matching a query.
        
        Args:
            query: Search query
            
        Returns:
            List of matching results
        """
        pass
