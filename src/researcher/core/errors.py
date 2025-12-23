"""
Custom exception hierarchy for the researcher application.

Provides specific exceptions for different error scenarios including research failures,
tier escalation, and LLM provider errors.
"""


class ResearchError(Exception):
    """Base exception for all research-related errors."""
    pass


class InsufficientResultsError(ResearchError):
    """
    Raised when Tier 1 research returns insufficient results.
    
    This error triggers escalation to Tier 2 if auto-escalation is enabled.
    """
    
    def __init__(self, message: str, source_count: int, min_required: int):
        super().__init__(message)
        self.source_count = source_count
        self.min_required = min_required


class LowConfidenceError(ResearchError):
    """
    Raised when research confidence is below threshold.
    
    This error triggers escalation to Tier 2 if auto-escalation is enabled.
    """
    
    def __init__(self, message: str, confidence: float, threshold: float):
        super().__init__(message)
        self.confidence = confidence
        self.threshold = threshold


class Tier2UnavailableError(ResearchError):
    """
    Raised when Tier 2 is requested but not available.
    
    This can happen if:
    - Tavily API key is not configured
    - tier2_enabled is False in settings
    """
    
    def __init__(self, reason: str):
        super().__init__(f"Tier 2 unavailable: {reason}")
        self.reason = reason


class LLMProviderError(Exception):
    """Base exception for LLM provider errors."""
    
    def __init__(self, provider: str, message: str):
        super().__init__(f"LLM Provider '{provider}' error: {message}")
        self.provider = provider


class LLMAPIKeyMissingError(LLMProviderError):
    """Raised when LLM API key is missing."""
    
    def __init__(self, provider: str):
        super().__init__(
            provider,
            f"API key not configured for provider '{provider}'. "
            f"Please set the appropriate environment variable."
        )


class LLMRequestError(LLMProviderError):
    """Raised when LLM API request fails."""
    
    def __init__(self, provider: str, status_code: int, message: str):
        super().__init__(provider, f"Request failed (status {status_code}): {message}")
        self.status_code = status_code


class LLMRateLimitError(LLMProviderError):
    """Raised when LLM API rate limit is exceeded."""
    
    def __init__(self, provider: str, retry_after: int | None = None):
        msg = "Rate limit exceeded"
        if retry_after:
            msg += f". Retry after {retry_after} seconds"
        super().__init__(provider, msg)
        self.retry_after = retry_after


class DataValidationError(Exception):
    """Raised when data validation fails."""
    
    def __init__(self, field: str, message: str):
        super().__init__(f"Validation error in field '{field}': {message}")
        self.field = field


class ResourceNotFoundError(Exception):
    """Raised when a requested resource is not found."""
    
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(f"{resource_type} not found: {resource_id}")
        self.resource_type = resource_type
        self.resource_id = resource_id


class WebSearchError(ResearchError):
    """Raised when web search fails."""
    
    def __init__(self, message: str, tier: str):
        super().__init__(f"Web search failed in {tier}: {message}")
        self.tier = tier


class ContentExtractionError(ResearchError):
    """Raised when content extraction from URL fails."""
    
    def __init__(self, url: str, reason: str):
        super().__init__(f"Failed to extract content from {url}: {reason}")
        self.url = url
        self.reason = reason


class CitationFormattingError(Exception):
    """Raised when citation formatting fails."""
    
    def __init__(self, format_type: str, reason: str):
        super().__init__(f"Failed to format citation as {format_type}: {reason}")
        self.format_type = format_type
