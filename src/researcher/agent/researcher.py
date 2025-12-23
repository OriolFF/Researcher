"""
PydanticAI agent with Tier 1 built-in tools.

Uses WebSearchTool and WebFetchTool for research with automatic citations.
"""

import time
from datetime import datetime

from pydantic_ai import Agent, RunContext
from pydantic_ai.models import KnownModelName
from researcher.agent.tools import ddg_search, format_ddg_as_sources

from researcher.core.config import settings
from researcher.core.logging import (
    log_research_request,
    log_research_result,
    log_tier_escalation,
    logger
)
from researcher.domain.models import (
    ResearchDepth,
    ResearchQuery,
    ResearchResult,
    ResearchTier,
    Source
)
from researcher.domain.services import EscalationService
from researcher.data.tier2.tavily_client import TavilyAdvancedClient


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
        self.model = self._get_model()
        
        # Configure Tier 1 agent
        self.agent = Agent(
            self.model,
            system_prompt=self._get_system_prompt(),
        )
        
        # Register the DuckDuckGo search tool
        @self.agent.tool
        async def search_web(ctx: RunContext[None], query: str) -> str:
            """
            Search the web for information using DuckDuckGo.
            Use this when you need up-to-date facts or historical details.
            """
            results = await ddg_search(query, max_results=settings.tier1_max_sources)
            if not results:
                return "No search results found."
            
            # Store sources in context for extraction later if needed
            # (Simplification for this implementation)
            self._last_sources = format_ddg_as_sources(results)
            
            formatted = "\n".join([f"[{i+1}] {r['title']}: {r['body']} (URL: {r['href']})" for i, r in enumerate(results)])
            return f"Search results for '{query}':\n{formatted}"

        # Initialize Tier 2 client
        self.tavily = TavilyAdvancedClient()
        self.escalation_service = EscalationService()
        
        logger.info(f"Tier 1 agent initialized with model: {settings.llm_provider.value}:{settings.llm_model}")
        self._last_sources = []

    
    def _get_model(self) -> any:
        """Get the model instance or name in PydanticAI format."""
        provider = settings.llm_provider.value
        model_name = settings.llm_model
        
        if provider == "ollama":
            logger.info(f"Using local Ollama model: {model_name} at {settings.ollama_base_url}")
            from pydantic_ai.models.ollama import OllamaModel
            return OllamaModel(
                model_name=model_name,
                base_url=f"{settings.ollama_base_url}/api" if not settings.ollama_base_url.endswith("/api") else settings.ollama_base_url
            )
        
        if provider == "openai":
            return f"openai:{model_name}"
        elif provider == "anthropic":
            return f"anthropic:{model_name}"
        elif provider == "gemini":
            return f"google-gla:gemini-1.5-flash"  # Standard PydanticAI name
        elif provider == "openrouter":
            return f"openrouter:{model_name}"
        else:
            return f"{provider}:{model_name}"

    
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
        Conduct research with the appropriate depth.
        
        Args:
            query: Research query with depth preference
            
        Returns:
            Research result
        """
        if query.depth == ResearchDepth.BASIC:
            return await self.basic_research(query)
        elif query.depth == ResearchDepth.DEEP:
            return await self.deep_research(query)
        else:
            return await self.comprehensive_research(query)

    async def basic_research(self, query: ResearchQuery) -> ResearchResult:
        """
        Conduct Tier 1 research only.
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
            
            findings = result.data if hasattr(result, 'data') else str(result)
            sources = self._extract_sources(result)
            citations = self._format_citations(sources)
            execution_time_ms = (time.time() - start_time) * 1000
            confidence = self._estimate_confidence(sources, findings)
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
            logger.error(f"Basic research failed: {e}")
            return self._create_error_result(query, start_time, str(e))

    async def deep_research(self, query: ResearchQuery) -> ResearchResult:
        """
        Conduct Tier 2 research directly.
        """
        if not settings.is_tier2_available():
            logger.warning("Tier 2 requested but not available. Falling back to Tier 1.")
            return await self.basic_research(query)
            
        start_time = time.time()
        
        log_research_request(
            query=query.query,
            depth="deep",
            tier="tier2"
        )
        
        try:
            # 1. Use Tavily for advanced search
            sources = await self.tavily.search(
                query=query.query,
                max_results=settings.tier2_max_sources
            )
            
            # 2. Get search context (Tavily optimizes this for LLMs)
            context = await self.tavily.get_search_context(query.query)
            
            # 3. Use the agent to synthesize findings from the deeper context
            # We inject the context into the prompt
            synthesis_prompt = f"""
            Using the following advanced research results, provide a comprehensive answer to the query: '{query.query}'
            
            ADVANCED RESEARCH RESULTS:
            {context}
            
            Include inline citations [1], [2], etc. corresponding to the sources provided.
            """
            
            result = await self.agent.run(synthesis_prompt)
            findings = result.data if hasattr(result, 'data') else str(result)
            
            citations = self._format_citations(sources)
            execution_time_ms = (time.time() - start_time) * 1000
            
            # Tier 2 usually has higher confidence due to more sources
            confidence = min(0.95, self._estimate_confidence(sources, findings) + 0.1)
            gaps = self._identify_gaps(findings, query.query)
            
            research_result = ResearchResult(
                query=query.query,
                findings=findings,
                sources=sources,
                citations=citations,
                confidence=confidence,
                tier_used=ResearchTier.TIER2,
                execution_time_ms=execution_time_ms,
                gaps=gaps,
            )
            
            log_research_result(
                tier_used="tier2",
                source_count=len(sources),
                confidence=confidence,
                execution_time_ms=execution_time_ms
            )
            
            return research_result
            
        except Exception as e:
            logger.error(f"Deep research failed: {e}")
            return self._create_error_result(query, start_time, str(e), tier=ResearchTier.TIER2)

    async def comprehensive_research(self, query: ResearchQuery) -> ResearchResult:
        """
        Perform research with automatic escalation.
        """
        # Step 1: Start with Tier 1
        tier1_result = await self.basic_research(query)
        
        # Step 2: Check if Tier 2 is even possible
        if not settings.is_tier2_available():
            return tier1_result
            
        # Step 3: Evaluate if escalation is needed
        decision = self.escalation_service.should_escalate(tier1_result, query)
        
        if not decision.should_escalate:
            return tier1_result
            
        # Step 4: Escalate to Tier 2
        log_tier_escalation(
            reason=decision.reason,
            from_tier="tier1",
            to_tier="tier2"
        )
        
        tier2_result = await self.deep_research(query)
        
        # Merge results or return Tier 2 (prefer Tier 2 as it's more definitive)
        # Note: We keep Tier 1 sources if they are unique
        all_sources = self._merge_sources(tier1_result.sources, tier2_result.sources)
        tier2_result.sources = all_sources
        tier2_result.citations = self._format_citations(all_sources)
        
        return tier2_result

    def _create_error_result(self, query, start_time, error_msg, tier=ResearchTier.TIER1):
        execution_time_ms = (time.time() - start_time) * 1000
        return ResearchResult(
            query=query.query,
            findings=f"Research failed: {error_msg}",
            sources=[],
            citations=[],
            confidence=0.0,
            tier_used=tier,
            execution_time_ms=execution_time_ms,
            gaps=["Complete research failure"],
        )

    def _merge_sources(self, s1: list[Source], s2: list[Source]) -> list[Source]:
        urls = {s.url for s in s2}
        merged = list(s2)
        for s in s1:
            if s.url not in urls:
                merged.append(s)
        return merged

    
    def _extract_sources(self, result: any) -> list[Source]:
        """Extract sources from agent result and context."""
        # For this implementation, we use the sources stored during the last tool call
        return self._last_sources

    
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
