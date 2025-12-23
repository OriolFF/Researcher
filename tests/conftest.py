"""Pytest configuration and shared fixtures."""

import pytest


@pytest.fixture
def sample_source():
    """Sample source for testing."""
    from researcher.domain import Source, ResearchTier
    
    return Source(
        url="https://example.com/article",
        title="Sample Historical Article",
        author="Test Author",
        publisher="Test Publisher",
        date_accessed="2025-12-23",
        credibility_score=0.8,
        tier=ResearchTier.TIER1
    )


@pytest.fixture
def sample_sources(sample_source):
    """List of sample sources."""
    from researcher.domain import Source
    
    return [
        sample_source,
        Source(url="https://example2.com", title="Source 2"),
        Source(url="https://example3.com", title="Source 3"),
    ]


@pytest.fixture
def sample_research_result(sample_sources):
    """Sample research result for testing."""
    from researcher.domain import ResearchResult, ResearchTier
    
    return ResearchResult(
        query="Sample historical query",
        findings="Sample findings about history",
        sources=sample_sources,
        citations=["Citation 1", "Citation 2"],
        confidence=0.8,
        tier_used=ResearchTier.TIER1,
        execution_time_ms=1500.0,
        gaps=[]
    )
