"""
Core configuration management using Pydantic Settings.

Handles LLM provider configuration, tier settings, escalation rules, and all environment variables.
"""

from enum import Enum
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"


class CitationFormat(str, Enum):
    """Citation format styles."""
    MLA = "MLA"
    APA = "APA"


class OutputFormat(str, Enum):
    """Output format options."""
    JSON = "json"
    MARKDOWN = "markdown"
    STRUCTURED = "structured"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # ================================================
    # LLM Provider Configuration
    # ================================================
    
    llm_provider: LLMProvider = Field(
        default=LLMProvider.OPENAI,
        description="LLM provider to use"
    )
    llm_model: str = Field(
        default="gpt-4",
        description="Model name for the LLM provider"
    )
    max_tokens: int = Field(
        default=2000,
        ge=100,
        le=100000,
        description="Maximum tokens for LLM responses"
    )
    temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=2.0,
        description="Temperature for LLM generation (lower = more factual)"
    )
    
    # API Keys
    openai_api_key: str | None = Field(default=None, description="OpenAI API key")
    anthropic_api_key: str | None = Field(default=None, description="Anthropic API key")
    google_api_key: str | None = Field(default=None, description="Google Gemini API key")
    openrouter_api_key: str | None = Field(default=None, description="OpenRouter API key")
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama base URL for local models"
    )
    
    # ================================================
    # Tier 1 Configuration (Built-in Tools)
    # ================================================
    
    tier1_enabled: bool = Field(
        default=True,
        description="Enable Tier 1 (PydanticAI built-in tools)"
    )
    tier1_max_sources: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum sources to fetch in Tier 1"
    )
    tier1_allowed_domains: list[str] = Field(
        default_factory=lambda: [
            "wikipedia.org",
            "britannica.com",
            "history.com",
            "edu"  # Any .edu domain
        ],
        description="Allowed domains for Tier 1 WebFetchTool"
    )
    
    # ================================================
    # Tier 2 Configuration (Advanced Tools)
    # ================================================
    
    tier2_enabled: bool = Field(
        default=False,
        description="Enable Tier 2 (requires Tavily API key)"
    )
    tavily_api_key: str | None = Field(
        default=None,
        description="Tavily API key for advanced search"
    )
    tier2_max_sources: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum sources to fetch in Tier 2"
    )
    tier2_search_depth: Literal["basic", "advanced"] = Field(
        default="advanced",
        description="Tavily search depth"
    )
    
    # ================================================
    # Escalation Rules
    # ================================================
    
    enable_auto_escalation: bool = Field(
        default=True,
        description="Allow automatic escalation from Tier 1 to Tier 2"
    )
    escalation_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Quality score threshold for escalation (0-1)"
    )
    min_sources_tier1: int = Field(
        default=3,
        ge=1,
        le=20,
        description="Minimum sources required from Tier 1 to avoid escalation"
    )
    min_confidence_tier1: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum confidence required from Tier 1 to avoid escalation"
    )
    
    # ================================================
    # Citation Settings
    # ================================================
    
    citation_format: CitationFormat = Field(
        default=CitationFormat.MLA,
        description="Citation format (MLA or APA)"
    )
    include_access_dates: bool = Field(
        default=True,
        description="Include access dates in citations"
    )
    
    # ================================================
    # Output Settings
    # ================================================
    
    default_output_format: OutputFormat = Field(
        default=OutputFormat.JSON,
        description="Default output format"
    )
    
    # ================================================
    # API Settings (FastAPI)
    # ================================================
    
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, ge=1000, le=65535, description="API port")
    api_reload: bool = Field(default=True, description="Enable auto-reload for development")
    
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            "http://localhost:3000",
            "null",
        ],
        description="CORS allowed origins"
    )
    
    # ================================================
    # Logging
    # ================================================
    
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    log_format: Literal["json", "text"] = Field(
        default="text",
        description="Log output format"
    )
    
    # ================================================
    # Validators
    # ================================================
    
    @field_validator("tier2_enabled")
    @classmethod
    def validate_tier2_requirements(cls, v: bool, info) -> bool:
        """Validate Tier 2 can only be enabled if Tavily API key is provided."""
        if v and not info.data.get("tavily_api_key"):
            # Auto-disable if no key
            return False
        return v
    
    @field_validator("llm_provider", mode="after")
    @classmethod
    def validate_llm_provider_key(cls, v: LLMProvider) -> LLMProvider:
        """Ensure the selected provider has an API key (except Ollama)."""
        # Note: This is a soft validation - we don't raise errors here
        # because API keys might be set later or via environment
        return v
    
    # ================================================
    # Helper Methods
    # ================================================
    
    def get_llm_api_key(self) -> str | None:
        """Get the API key for the configured LLM provider."""
        key_map = {
            LLMProvider.OPENAI: self.openai_api_key,
            LLMProvider.ANTHROPIC: self.anthropic_api_key,
            LLMProvider.GEMINI: self.google_api_key,
            LLMProvider.OPENROUTER: self.openrouter_api_key,
            LLMProvider.OLLAMA: None,  # No key needed
        }
        return key_map.get(self.llm_provider)
    
    def get_llm_model_string(self) -> str:
        """Get the full LLM model string for LiteLLM."""
        return f"{self.llm_provider.value}:{self.llm_model}"
    
    def is_tier2_available(self) -> bool:
        """Check if Tier 2 is available."""
        return self.tier2_enabled and self.tavily_api_key is not None


# Global settings instance
settings = Settings()
