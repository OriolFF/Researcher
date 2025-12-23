"""Tests for domain layer models and services."""

import pytest

from researcher.core.config import settings
from researcher.domain import (
    CitationFormatter,
    EscalationService,
    HistoricalPeriod,
    ResearchDepth,
    ResearchQuery,
    ResearchResult,
    ResearchTier,
    Source,
    ValidationService,
)


class TestModels:
    """Test domain models."""
    
    def test_source_creation(self):
        """Test creating a source with required fields."""
        source = Source(
            url="https://example.com",
            title="Test Source",
        )
        assert source.url == "https://example.com"
        assert source.title == "Test Source"
        assert source.tier == ResearchTier.TIER1
        assert 0.0 <= source.credibility_score <= 1.0
    
    def test_research_query_creation(self):
        """Test creating a research query."""
        query = ResearchQuery(
            query="Battle of Waterloo",
            depth=ResearchDepth.AUTO
        )
        assert query.query == "Battle of Waterloo"
        assert query.depth == ResearchDepth.AUTO
    
    def test_research_result_properties(self):
        """Test research result properties."""
        result = ResearchResult(
            query="Test query",
            findings="Test findings",
            sources=[
                Source(url="https://example.com", title="Source 1"),
                Source(url="https://example2.com", title="Source 2"),
            ],
            confidence=0.85,
            tier_used=ResearchTier.TIER1,
            execution_time_ms=1500.0
        )
        
        assert result.source_count == 2
        assert result.is_high_confidence is True
        assert result.is_low_confidence is False


class TestEscalationService:
    """Test escalation decision logic."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.service = EscalationService()
    
    def test_no_escalation_when_sufficient(self):
        """Test that good Tier 1 results don't trigger escalation."""
        query = ResearchQuery(query="Test", depth=ResearchDepth.AUTO)
        result = ResearchResult(
            query="Test",
            findings="Good findings",
            sources=[
                Source(url=f"https://example{i}.com", title=f"Source {i}")
                for i in range(5)  # 5 sources (> min_sources_tier1)
            ],
            confidence=0.85,  # High confidence
            tier_used=ResearchTier.TIER1,
            execution_time_ms=1000.0,
            gaps=[],  # No gaps
        )
        
        decision = self.service.should_escalate(result, query)
        assert decision.should_escalate is False
        assert decision.quality_score >= self.service.threshold
    
    def test_escalation_on_insufficient_sources(self):
        """Test escalation when source count is too low."""
        query = ResearchQuery(query="Test", depth=ResearchDepth.AUTO)
        result = ResearchResult(
            query="Test",
            findings="Limited findings",
            sources=[Source(url="https://example.com", title="Only Source")],
            confidence=0.8,
            tier_used=ResearchTier.TIER1,
            execution_time_ms=1000.0
        )
        
        decision = self.service.should_escalate(result, query)
        assert decision.should_escalate is True
        assert "Insufficient sources" in decision.reason
    
    def test_escalation_on_low_confidence(self):
        """Test escalation when confidence is low."""
        query = ResearchQuery(query="Test", depth=ResearchDepth.AUTO)
        result = ResearchResult(
            query="Test",
            findings="Uncertain findings",
            sources=[
                Source(url=f"https://example{i}.com", title=f"Source {i}")
                for i in range(5)
            ],
            confidence=0.5,  # Low confidence
            tier_used=ResearchTier.TIER1,
            execution_time_ms=1000.0
        )
        
        decision = self.service.should_escalate(result, query)
        assert decision.should_escalate is True
        assert "Low confidence" in decision.reason


class TestCitationFormatter:
    """Test citation formatting."""
    
    def test_mla_citation(self):
        """Test MLA citation format."""
        formatter = CitationFormatter(format_type="MLA")
        source = Source(
            url="https://britannica.com/battle-waterloo",
            title="Battle of Waterloo",
            author="John Smith",
            date_accessed="2025-12-23"
        )
        
        citation = formatter.format_citation(source)
        assert "John Smith" in citation
        assert "Battle of Waterloo" in citation
        assert "https://britannica.com/battle-waterloo" in citation
    
    def test_apa_citation(self):
        """Test APA citation format."""
        formatter = CitationFormatter(format_type="APA")
        source = Source(
            url="https://britannica.com/battle-waterloo",
            title="Battle of Waterloo",
            author="Smith, J.",
            date_published="2020"
        )
        
        citation = formatter.format_citation(source)
        assert "Smith, J." in citation
        assert "(2020)" in citation
        assert "Battle of Waterloo" in citation


class TestValidationService:
    """Test validation service."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.service = ValidationService()
    
    def test_historical_date_valid(self):
        """Test validation of valid historical date."""
        assert self.service.validate_historical_date("Battle of Waterloo", "1815-06-18")
    
    def test_historical_date_invalid_future(self):
        """Test rejection of future dates."""
        assert not self.service.validate_historical_date("Future Event", "2050-01-01")
    
    def test_source_credibility_high(self):
        """Test high credibility for known domains."""
        source = Source(
            url="https://wikipedia.org/wiki/History",
            title="History Article",
            author="Wikipedia Contributors",
            publisher="Wikipedia"
        )
        
        credibility = self.service.assess_source_credibility(source)
        assert credibility > 0.7  # Should be high
    
    def test_source_credibility_unknown(self):
        """Test moderate credibility for unknown domains."""
        source = Source(
            url="https://unknown-blog.com/article",
            title="Random Article"
        )
        
        credibility = self.service.assess_source_credibility(source)
        assert 0.3 <= credibility <= 0.7  # Should be moderate
