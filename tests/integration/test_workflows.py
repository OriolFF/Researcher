"""Integration tests for research workflows."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from researcher.agent.researcher import ResearchAgent
from researcher.domain.models import ResearchDepth, ResearchQuery, ResearchResult, ResearchTier, Source


from researcher.core.config import settings

@pytest.fixture
def agent():
    # Set dummy keys directly on the settings object for testing
    settings.openai_api_key = "sk-dummy"
    settings.tavily_api_key = "tvly-dummy"
    
    with patch("researcher.agent.researcher.Agent"):
        return ResearchAgent()


class TestResearchWorkflows:
    """Test research workflows and escalation."""
    
    @pytest.mark.asyncio
    async def test_basic_research_flow(self, agent):
        """Test basic Tier 1 research flow."""
        query = ResearchQuery(query="Test query", depth=ResearchDepth.BASIC)
        
        # Mock the PydanticAI agent run
        mock_result = MagicMock()
        mock_result.data = "These are basic findings."
        agent.agent.run = AsyncMock(return_value=mock_result)
        
        # Mock source extraction
        agent._last_sources = [Source(url="https://test.com", title="Test")]
        
        result = await agent.research(query)
        
        assert isinstance(result, ResearchResult)
        assert result.findings == "These are basic findings."
        assert result.tier_used == ResearchTier.TIER1
        assert len(result.sources) == 1
        agent.agent.run.assert_awaited_once_with("Test query")

    @pytest.mark.asyncio
    async def test_deep_research_flow(self, agent):
        """Test deep Tier 2 research flow."""
        query = ResearchQuery(query="Deep query", depth=ResearchDepth.DEEP)
        
        # Enable Tier 2 directly
        settings.tier2_enabled = True
        settings.tavily_api_key = "tvly-dummy"
        
        # Mock Tavily client
        agent.tavily.search = AsyncMock(return_value=[Source(url="https://deep.com", title="Deep Source")])
        agent.tavily.get_search_context = AsyncMock(return_value="Deep context content")
            
        # Mock the PydanticAI agent synthesis
        mock_result = MagicMock()
        mock_result.data = "These are synthesized deep findings."
        agent.agent.run = AsyncMock(return_value=mock_result)
        
        result = await agent.research(query)
        
        assert result.tier_used == ResearchTier.TIER2
        assert result.findings == "These are synthesized deep findings."
        assert len(result.sources) >= 1
        agent.tavily.search.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_auto_escalation_flow(self, agent):
        """Test automatic escalation from Tier 1 to Tier 2."""
        query = ResearchQuery(query="Complex query", depth=ResearchDepth.AUTO)
        
        # Enable Tier 2 directly
        settings.tier2_enabled = True
        settings.tavily_api_key = "tvly-dummy"
        
        # 1. Mock Tier 1 to return poor results (1 source)
        mock_tier1_result = MagicMock()
        mock_tier1_result.data = "Limited findings."
        agent.agent.run = AsyncMock(side_effect=[
            mock_tier1_result, # Tier 1 run
            MagicMock(data="Enhanced deep findings.") # Tier 2 synthesis run
        ])
        
        # Mock source extraction for Tier 1
        with patch.object(agent, "_extract_sources", return_value=[Source(url="https://poor.com", title="Poor")]):
            # Mock Tavily for Tier 2
            agent.tavily.search = AsyncMock(return_value=[Source(url="https://rich.com", title="Rich")])
            agent.tavily.get_search_context = AsyncMock(return_value="Rich context")
            
            result = await agent.research(query)
            
            # Check that escalation happened
            assert result.tier_used == ResearchTier.TIER2
            assert result.findings == "Enhanced deep findings."
            assert any(s.url == "https://rich.com" for s in result.sources)
            assert any(s.url == "https://poor.com" for s in result.sources) # Merged
            assert agent.agent.run.call_count == 2
