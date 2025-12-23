"""
Domain services implementing business logic.

Contains services for research orchestration, escalation decisions, validation, and citation formatting.
"""

from datetime import datetime

from researcher.core.config import settings
from researcher.core.errors import InsufficientResultsError, LowConfidenceError
from researcher.domain.models import (
    EscalationDecision,
    HistoricalPeriod,
    ResearchQuery,
    ResearchResult,
    ResearchTier,
    Source,
)


class EscalationService:
    """
    Service for deciding when to escalate from Tier 1 to Tier 2.
    
    Evaluates research quality based on multiple factors:
    - Number of sources found
    - Confidence level
    - Source diversity
    - Information gaps
    """
    
    def __init__(self):
        self.threshold = settings.escalation_threshold
        self.min_sources = settings.min_sources_tier1
        self.min_confidence = settings.min_confidence_tier1
    
    def should_escalate(
        self,
        tier1_result: ResearchResult,
        query: ResearchQuery,
    ) -> EscalationDecision:
        """
        Determine if escalation to Tier 2 is warranted.
        
        Args:
            tier1_result: Result from Tier 1 research
            query: Original query
            
        Returns:
            Escalation decision with reasoning
        """
        quality_score = self._calculate_quality_score(tier1_result)
        
        # Check if escalation is needed
        reasons = []
        
        if tier1_result.source_count < self.min_sources:
            reasons.append(
                f"Insufficient sources ({tier1_result.source_count} < {self.min_sources})"
            )
        
        if tier1_result.confidence < self.min_confidence:
            reasons.append(
                f"Low confidence ({tier1_result.confidence:.2f} < {self.min_confidence})"
            )
        
        if len(tier1_result.gaps) > 0:
            reasons.append(
                f"Information gaps identified: {len(tier1_result.gaps)} items"
            )
        
        if quality_score < self.threshold:
            reasons.append(
                f"Overall quality score below threshold ({quality_score:.2f} < {self.threshold})"
            )
        
        should_escalate = len(reasons) > 0
        reason = "; ".join(reasons) if reasons else "Tier 1 results sufficient"
        
        return EscalationDecision(
            should_escalate=should_escalate,
            reason=reason,
            tier1_result=tier1_result,
            quality_score=quality_score,
        )
    
    def _calculate_quality_score(self, result: ResearchResult) -> float:
        """
        Calculate overall quality score (0.0-1.0).
        
        Factors:
        - Source count (40% weight)
        - Confidence (40% weight)
        - Information completeness (20% weight)
        """
        # Source score: normalize to 0-1 based on min_sources
        source_score = min(result.source_count / self.min_sources, 1.0)
        
        # Confidence score: use directly
        confidence_score = result.confidence
        
        # Completeness score: inverse of gaps (fewer gaps = higher score)
        max_expected_gaps = 3  # Arbitrary threshold
        gaps_penalty = min(len(result.gaps) / max_expected_gaps, 1.0)
        completeness_score = 1.0 - gaps_penalty
        
        # Weighted average
        quality = (
            source_score * 0.4 +
            confidence_score * 0.4 +
            completeness_score * 0.2
        )
        
        return quality


class ValidationService:
    """
    Service for validating historical accuracy and fact-checking.
    """
    
    def validate_historical_date(self, event: str, date: str) -> bool:
        """
        Validate if a date is plausible for a historical event.
        
        Args:
            event: Event description
            date: Date string
            
        Returns:
            True if date seems valid
        """
        # TODO: Implement actual validation logic
        # For now, basic sanity check
        try:
            year = int(date.split("-")[0])
            return -3000 <= year <= datetime.now().year
        except (ValueError, IndexError):
            return False
    
    def assess_source_credibility(self, source: Source) -> float:
        """
        Assess credibility of a source based on domain and metadata.
        
        Args:
            source: Source to assess
            
        Returns:
            Credibility score (0.0-1.0)
        """
        score = 0.5  # Base score
        
        # Higher credibility for known domains
        high_credibility_domains = [
            "wikipedia.org",
            "britannica.com",
            ".edu",
            ".gov",
            "jstor.org",
            "archive.org",
        ]
        
        for domain in high_credibility_domains:
            if domain in source.url:
                score += 0.2
                break
        
        # Bonus for having author and publisher
        if source.author:
            score += 0.1
        if source.publisher:
            score += 0.1
        
        # Bonus for recent access (source is up-to-date)
        if source.date_accessed:
            score += 0.1
        
        return min(score, 1.0)
    
    def cross_reference_facts(
        self,
        fact: str,
        sources: list[Source]
    ) -> tuple[bool, int]:
        """
        Check if a fact is mentioned across multiple sources.
        
        Args:
            fact: Fact to verify
            sources: List of sources
            
        Returns:
            (is_verified, mention_count)
        """
        # TODO: Implement actual cross-referencing
        # This would require comparing fact against source content
        # For now, placeholder
        mention_count = len(sources)  # Assume all sources mention it
        is_verified = mention_count >= 2
        
        return is_verified, mention_count


class CitationFormatter:
    """
    Service for formatting citations in MLA or APA style.
    """
    
    def __init__(self, format_type: str = "MLA"):
        self.format_type = format_type.upper()
    
    def format_citation(self, source: Source) -> str:
        """
        Format a single source as a citation.
        
        Args:
            source: Source to format
            
        Returns:
            Formatted citation string
        """
        if self.format_type == "MLA":
            return self._format_mla(source)
        elif self.format_type == "APA":
            return self._format_apa(source)
        else:
            return self._format_mla(source)  # Default to MLA
    
    def format_citations(self, sources: list[Source]) -> list[str]:
        """
        Format multiple sources as citations.
        
        Args:
            sources: List of sources
            
        Returns:
            List of formatted citations
        """
        return [self.format_citation(source) for source in sources]
    
    def _format_mla(self, source: Source) -> str:
        """Format citation in MLA style."""
        parts = []
        
        # Author (if available)
        if source.author:
            parts.append(f"{source.author}.")
        
        # Title
        parts.append(f'"{source.title}."')
        
        # Publisher (if available)
        if source.publisher:
            parts.append(f"{source.publisher},")
        
        # URL
        parts.append(source.url + ".")
        
        # Access date (if enabled)
        if settings.include_access_dates and source.date_accessed:
            parts.append(f"Accessed {self._format_date_mla(source.date_accessed)}.")
        
        return " ".join(parts)
    
    def _format_apa(self, source: Source) -> str:
        """Format citation in APA style."""
        parts = []
        
        # Author (if available)
        if source.author:
            parts.append(f"{source.author}.")
        
        # Date (if available)
        if source.date_published:
            parts.append(f"({source.date_published}).")
        
        # Title
        parts.append(f"{source.title}.")
        
        # Publisher (if available)
        if source.publisher:
            parts.append(f"{source.publisher}.")
        
        # URL
        parts.append(source.url)
        
        return " ".join(parts)
    
    def _format_date_mla(self, date_str: str) -> str:
        """Format date for MLA (e.g., '23 Dec. 2025')."""
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            return date_obj.strftime("%d %b. %Y")
        except ValueError:
            return date_str


class ContextBuilder:
    """
    Service for building story context from research results.
    """
    
    def build_story_context(
        self,
        result: ResearchResult,
        period: HistoricalPeriod | None = None
    ) -> dict[str, any]:
        """
        Extract story-relevant context from research.
        
        Args:
            result: Research result
            period: Historical period (if known)
            
        Returns:
            Dictionary with story context elements
        """
        context = {
            "setting": self._extract_setting(result, period),
            "key_figures": self._extract_key_figures(result),
            "major_events": self._extract_major_events(result),
            "atmosphere": self._extract_atmosphere(result),
            "daily_life_details": self._extract_daily_life(result),
            "sources": result.sources,
        }
        
        return context
    
    def _extract_setting(
        self,
        result: ResearchResult,
        period: HistoricalPeriod | None
    ) -> str:
        """Extract time and place setting."""
        if period and period.era_name:
            return f"During {period.era_name}"
        return "Historical period from research findings"
    
    def _extract_key_figures(self, result: ResearchResult) -> list[str]:
        """Extract important historical figures mentioned."""
        # TODO: Use NLP to extract named entities
        # Placeholder implementation
        return []
    
    def _extract_major_events(self, result: ResearchResult) -> list[str]:
        """Extract major historical events."""
        # TODO: Use NLP to extract events
        # Placeholder implementation
        return []
    
    def _extract_atmosphere(self, result: ResearchResult) -> str:
        """Extract mood and atmosphere from historical context."""
        # TODO: Analyze findings for atmospheric details
        return "Authentic historical atmosphere based on research"
    
    def _extract_daily_life(self, result: ResearchResult) -> list[str]:
        """Extract daily life details."""
        # TODO: Extract specific details about daily life
        return []
