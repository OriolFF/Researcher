"""Core package initialization."""

from researcher.core.config import settings
from researcher.core.errors import (
    CitationFormattingError,
    ContentExtractionError,
    DataValidationError,
    InsufficientResultsError,
    LLMAPIKeyMissingError,
    LLMProviderError,
    LLMRateLimitError,
    LLMRequestError,
    LowConfidenceError,
    ResearchError,
    ResourceNotFoundError,
    Tier2UnavailableError,
    WebSearchError,
)
from researcher.core.logging import (
    log_error,
    log_llm_request,
    log_research_request,
    log_research_result,
    log_tier_escalation,
    logger,
    setup_logging,
)

__all__ = [
    # Config
    "settings",
    # Logging
    "logger",
    "setup_logging",
    "log_research_request",
    "log_tier_escalation",
    "log_research_result",
    "log_llm_request",
    "log_error",
    # Errors
    "ResearchError",
    "InsufficientResultsError",
    "LowConfidenceError",
    "Tier2UnavailableError",
    "LLMProviderError",
    "LLMAPIKeyMissingError",
    "LLMRequestError",
    "LLMRateLimitError",
    "DataValidationError",
    "ResourceNotFoundError",
    "WebSearchError",
    "ContentExtractionError",
    "CitationFormattingError",
]
