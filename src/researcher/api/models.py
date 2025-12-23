"""
FastAPI request and response models.
"""

from pydantic import BaseModel, Field

from researcher.domain.models import ResearchDepth, Source


class ResearchRequest(BaseModel):
    """Request model for research endpoint."""
    query: str = Field(..., min_length=1, description="Research query")
    output_format: str = Field(default="json", description="Output format (json/markdown/structured)")
    llm_provider: str | None = Field(None, description="LLM provider override")
    llm_model: str | None = Field(None, description="LLM model override")
    citation_format: str = Field(default="MLA", description="Citation format (MLA/APA)")
    depth: ResearchDepth = Field(default=ResearchDepth.AUTO, description="Research depth")


class ResearchResponse(BaseModel):
    """Response model for research results."""
    query: str
    findings: str
    sources: list[Source]
    citations: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
    tier_used: str
    execution_time_ms: float
    gaps: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    tier1_available: bool
    tier2_available: bool
    llm_provider: str
    llm_model: str


class ErrorResponse(BaseModel):
    """Error response model."""
    detail: str
    error_type: str | None = None
