"""
FastAPI routes for the research API.
"""

from fastapi import APIRouter, HTTPException

from researcher.agent.researcher import ResearchAgent
from researcher.api.models import (
    ErrorResponse,
    HealthResponse,
    ResearchRequest,
    ResearchResponse,
)
from researcher.core.config import settings
from researcher.core.errors import ResearchError
from researcher.core.logging import logger
from researcher.domain.models import ResearchQuery

router = APIRouter()

# Initialize agent (singleton)
_agent: ResearchAgent | None = None


def get_agent() -> ResearchAgent:
    """Get or create the research agent."""
    global _agent
    if _agent is None:
        _agent = ResearchAgent()
    return _agent


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns system status and tier availability.
    """
    return HealthResponse(
        status="healthy",
        tier1_available=settings.tier1_enabled,
        tier2_available=settings.is_tier2_available(),
        llm_provider=settings.llm_provider.value,
        llm_model=settings.llm_model,
    )


@router.post("/research", response_model=ResearchResponse)
async def research(request: ResearchRequest):
    """
    Research endpoint with auto-escalation.
    
    Starts with Tier 1, escalates to Tier 2 if needed.
    """
    try:
        logger.info(f"Research request: {request.query[:50]}...")
        
        # Create research query
        query = ResearchQuery(
            query=request.query,
            depth=request.depth,
        )
        
        # Get agent and conduct research
        agent = get_agent()
        result = await agent.research(query)
        
        # Convert to API response
        return ResearchResponse(
            query=result.query,
            findings=result.findings,
            sources=result.sources,
            citations=result.citations,
            confidence=result.confidence,
            tier_used=result.tier_used.value,
            execution_time_ms=result.execution_time_ms,
            gaps=result.gaps,
        )
        
    except ResearchError as e:
        logger.error(f"Research error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/research/basic", response_model=ResearchResponse)
async def research_basic(request: ResearchRequest):
    """
    Basic research endpoint (Tier 1 only).
    
    Fast research using only built-in tools.
    """
    # Force basic depth
    request.depth = "basic"
    return await research(request)


@router.post("/research/deep", response_model=ResearchResponse)
async def research_deep(request: ResearchRequest):
    """
    Deep research endpoint (Tier 2 if available).
    
    Thorough research using advanced tools.
    """
    if not settings.is_tier2_available():
        raise HTTPException(
            status_code=503,
            detail="Tier 2 unavailable. Please configure TAVILY_API_KEY."
        )
    
    # Force deep depth
    request.depth = "deep"
    return await research(request)
