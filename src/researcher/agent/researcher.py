"""
PydanticAI agent with Tier 1 built-in tools.

Uses WebSearchTool and WebFetchTool for research with automatic citations.
"""

import time
from datetime import datetime

from pydantic_ai import Agent
from pydantic_ai.models import KnownModelName

from researcher.core.config import settings
from researcher.core.logging import log_research_request, log_research_result, logger
from researcher.domain.models import ResearchQuery, ResearchResult, ResearchTier, Source


class ResearchAgent:
    """
    Tier 1 research agent using PydanticAI built-in tools.
    
    Features:
    - WebSearchTool for web search
    - WebFetchTool for content extraction with citations
    - LLM-agnostic via LiteLLM
    """
    
    def __init__(self):
        """Initialize the research agent with Tier 1 tools."""
        self.model_name = self._get_model_name()
        
        # Import built-in tools
        try:
            from pydantic_ai import WebSearchTool, WebFetchTool
            
            # Configure Tier 1 agent with built-in tools
            self.agent = Agent(
                self.model_name,
                builtin_tools=[
                    WebSearchTool(),
                    WebFetchTool(
                        enable_citations=True,
                        allowed_domains=settings.tier1_allowed_domains,
                        max_uses=settings.tier1_max_sources,
                    )
                ],
                system_prompt=self._get_system_prompt(),
            )
            
            logger.info(f"Tier 1 agent initialized with model: {self.model_name}")
            
        except ImportError as e:
            logger.error(f"Failed to import PydanticAI built-in tools: {e}")
            # Fallback: create agent without built-in tools
            self.agent = Agent(
                self.model_name,
                system_prompt=self._get_system_prompt(),
            )
            logger.warning("Agent created without built-in tools (import error)")
    
    def _get_model_name(self) -> str:
        """Get the model name in PydanticAI format."""
        provider = settings.llm_provider.value
        model = settings.llm_model
        
        # PydanticAI uses format: "provider:model"
        # But for some providers, it expects specific formats
        if provider == "openai":
            return f"openai:{model}"
        elif provider == "anthropic":
            return f"anthropic:{model}"
        elif provider == "gemini":
            return f"gemini-1.5-flash"  # PydanticAI expects specific format
        elif provider == "openrouter":
            return f"openrouter/{model}"
        elif provider == "ollama":
            return f"ollama:{model}"
        else:
            return f"{provider}:{model}"
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for Tier 1 research."""
        return """You are a historical research assistant helping writers create historically accurate stories.

Your role:
1. Search for factual historical information using web search
2. Fetch and analyze content from reliable sources
3. Provide citations for all claims
4. Verify dates, events, and historical figures
5. Identify any gaps in available information
6. Assess your confidence in findings

When researching:
- Prioritize reliable sources (Wikipedia, Britannica, .edu domains, historical societies)
- Always include proper citations
- Note any conflicting information from different sources
- Indicate confidence levels (high/medium/low)
- Flag when you need more sources or deeper research
- Focus on factual accuracy over creative interpretation

Output format:
- Main findings with inline citations [1], [2], etc.
- List of sources with full URLs
- Confidence assessment (0.0-1.0)
- Any gaps or uncertainties identified
- Historical period/era if applicable

Remember: You are using built-in web search and fetch tools. Use them to find accurate, cited information."""
    
    async def research(self, query: ResearchQuery) -> ResearchResult:
        """
        Conduct Tier 1 research using built-in tools.
        
        Args:
            query: Research query
            
        Returns:
            Research result with sources and citations
        """
        start_time = time.time()
        
        log_research_request(
            query=query.query,
            depth=query.depth.value,
            tier="tier1"
        )
        
        try:
            # Run the agent
            result = await self.agent.run(query.query)
            
            # Parse the result
            # Note: PydanticAI's built-in tools automatically include sources
            # We need to extract them from the result
            
            findings = result.data if hasattr(result, 'data') else str(result)
            
            # Extract sources from result (if available)
            sources = self._extract_sources(result)
            
            # Generate citations
            citations = self._format_citations(sources)
            
            # Calculate execution time
            execution_time_ms = (time.time() - start_time) * 1000
            
            # Estimate confidence (can be refined based on source quality)
            confidence = self._estimate_confidence(sources, findings)
            
            # Identify gaps (basic implementation)
            gaps = self._identify_gaps(findings, query.query)
            
            research_result = ResearchResult(
                query=query.query,
                findings=findings,
                sources=sources,
                citations=citations,
                confidence=confidence,
                tier_used=ResearchTier.TIER1,
                execution_time_ms=execution_time_ms,
                gaps=gaps,
            )
            
            log_research_result(
                tier_used="tier1",
                source_count=len(sources),
                confidence=confidence,
                execution_time_ms=execution_time_ms
            )
            
            return research_result
            
        except Exception as e:
            logger.error(f"Tier 1 research failed: {e}")
            
            # Return minimal result on error
            execution_time_ms = (time.time() - start_time) * 1000
            return ResearchResult(
                query=query.query,
                findings=f"Research failed: {str(e)}",
                sources=[],
                citations=[],
                confidence=0.0,
                tier_used=ResearchTier.TIER1,
                execution_time_ms=execution_time_ms,
                gaps=["Complete research failure - all information unavailable"],
            )
    
    def _extract_sources(self, result: any) -> list[Source]:
        """Extract sources from agent result."""
        sources = []
        
        # Try to extract from result metadata
        # This depends on PydanticAI's actual structure
        # For now, placeholder implementation
        
        # TODO: Properly extract from PydanticAI result when built-in tools provide sources
        
        return sources
    
    def _format_citations(self, sources: list[Source]) -> list[str]:
        """Format sources as citations."""
        from researcher.domain.services import CitationFormatter
        
        formatter = CitationFormatter(format_type=settings.citation_format.value)
        return formatter.format_citations(sources)
    
    def _estimate_confidence(self, sources: list[Source], findings: str) -> float:
        """Estimate confidence based on sources and findings."""
        if len(sources) == 0:
            return 0.0
        elif len(sources) >= 5:
            return 0.9
        elif len(sources) >= 3:
            return 0.75
        else:
            return 0.5
    
    def _identify_gaps(self, findings: str, query: str) -> list[str]:
        """Identify information gaps in findings."""
        gaps = []
        
        # Basic heuristics for gap detection
        uncertainty_phrases = [
            "unclear",
            "uncertain",
            "unknown",
            "not enough information",
            "limited sources",
            "contradictory",
        ]
        
        findings_lower = findings.lower()
        for phrase in uncertainty_phrases:
            if phrase in findings_lower:
                gaps.append(f"Uncertainty detected: {phrase}")
        
        return gaps
