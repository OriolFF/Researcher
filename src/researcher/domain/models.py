"""
Domain models for the historical researcher.

Defines core entities including research queries, results, sources, and tier information.
All models are framework-agnostic Pydantic models.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ResearchTier(str, Enum):
    """Research tier levels."""
    TIER1 = "tier1"  # Built-in PydanticAI tools (fast)
    TIER2 = "tier2"  # Advanced tools with Tavily (thorough)


class ResearchDepth(str, Enum):
    """Research depth preference."""
    BASIC = "basic"      # Force Tier 1 only
    AUTO = "auto"        # Auto-escalate if needed (recommended)
    DEEP = "deep"        # Force Tier 2 (if available)


class HistoricalPeriod(BaseModel):
    """Represents a specific historical time period."""
    start_year: int | None = Field(None, description="Start year (BCE is negative)")
    end_year: int | None = Field(None, description="End year (BCE is negative)")
    era_name: str | None = Field(None, description="Name of the era (e.g., 'Napoleonic Wars')")
    century: str | None = Field(None, description="Century (e.g., '19th century')")


class Source(BaseModel):
    """Represents a research source with citation information."""
    url: str = Field(..., description="Source URL")
    title: str = Field(..., description="Source title")
    author: str | None = Field(None, description="Author name")
    publisher: str | None = Field(None, description="Publisher")
    date_published: str | None = Field(None, description="Publication date")
    date_accessed: str = Field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d"),
        description="Date accessed"
    )
    credibility_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Source credibility (0.0-1.0)"
    )
    tier: ResearchTier = Field(
        default=ResearchTier.TIER1,
        description="Tier that found this source"
    )


class ResearchQuery(BaseModel):
    """User's research request."""
    query: str = Field(..., min_length=1, description="Research question or topic")
    depth: ResearchDepth = Field(
        default=ResearchDepth.AUTO,
        description="Research depth preference"
    )
    historical_period: HistoricalPeriod | None = Field(
        None,
        description="Optional time period constraint"
    )
    max_sources: int | None = Field(
        None,
        ge=1,
        le=50,
        description="Maximum number of sources to return"
    )


class ResearchResult(BaseModel):
    """Structured research findings."""
    query: str = Field(..., description="Original research query")
    findings: str = Field(..., description="Main research findings")
    sources: list[Source] = Field(
        default_factory=list,
        description="List of sources"
    )
    citations: list[str] = Field(
        default_factory=list,
        description="Formatted citations (MLA/APA)"
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence in findings (0.0-1.0)"
    )
    tier_used: ResearchTier = Field(
        ...,
        description="Tier that generated this result"
    )
    execution_time_ms: float = Field(
        ...,
        ge=0,
        description="Execution time in milliseconds"
    )
    historical_period: HistoricalPeriod | None = Field(
        None,
        description="Detected historical period"
    )
    gaps: list[str] = Field(
        default_factory=list,
        description="Identified information gaps"
    )
    
    @property
    def source_count(self) -> int:
        """Get number of sources."""
        return len(self.sources)
    
    @property
    def is_high_confidence(self) -> bool:
        """Check if confidence is high (>= 0.8)."""
        return self.confidence >= 0.8
    
    @property
    def is_low_confidence(self) -> bool:
        """Check if confidence is low (< 0.6)."""
        return self.confidence < 0.6


class EscalationDecision(BaseModel):
    """Decision to escalate from Tier 1 to Tier 2."""
    should_escalate: bool = Field(..., description="Whether to escalate")
    reason: str = Field(..., description="Reason for escalation decision")
    tier1_result: ResearchResult | None = Field(
        None,
        description="Tier 1 result that triggered escalation"
    )
    quality_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Quality score of Tier 1 result"
    )


class StoryContext(BaseModel):
    """Historical context formatted for story writing."""
    setting: str = Field(..., description="Time and place setting")
    key_figures: list[str] = Field(
        default_factory=list,
        description="Important historical figures"
    )
    major_events: list[str] = Field(
        default_factory=list,
        description="Major historical events"
    )
    atmosphere: str = Field(..., description="Historical atmosphere and mood")
    daily_life_details: list[str] = Field(
        default_factory=list,
        description="Details about daily life"
    )
    sources: list[Source] = Field(
        default_factory=list,
        description="Reference sources for verification"
    )
