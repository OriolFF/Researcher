"""
LiteLLM client wrapper implementing the LLMProvider port.

Provides a unified interface to multiple LLM providers (OpenAI, Anthropic, Gemini, etc.)
"""

from typing import Any

import litellm
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

from researcher.core.config import settings
from researcher.core.errors import LLMAPIKeyMissingError, LLMProviderError, LLMRateLimitError
from researcher.core.logging import log_llm_request, logger


class LiteLLMClient:
    """
    LiteLLM client for LLM provider abstraction.
    
    Supports: OpenAI, Anthropic, Google Gemini, OpenRouter, Ollama
    """
    
    def __init__(self):
        self.provider = settings.llm_provider.value
        self.model = settings.get_llm_model_string()
        self.api_key = settings.get_llm_api_key()
        
        # Set API key for litellm
        if self.api_key:
            if self.provider == "openai":
                litellm.openai_key = self.api_key
            elif self.provider == "anthropic":
                litellm.anthropic_key = self.api_key
            elif self.provider == "gemini":
                litellm.gemini_key = self.api_key
            elif self.provider == "openrouter":
                litellm.openrouter_key = self.api_key
        
        # Configure LiteLLM
        litellm.drop_params = True  # Drop unsupported params instead of failing
        litellm.set_verbose = False  # Disable verbose logging
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def complete(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """
        Generate a completion from the LLM.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (uses settings default if None)
            max_tokens: Max tokens (uses settings default if None)
            
        Returns:
            Generated text response
            
        Raises:
            LLMProviderError: If the request fails
            LLMRateLimitError: If rate limit is exceeded
        """
        try:
            temp = temperature if temperature is not None else settings.temperature
            tokens = max_tokens if max_tokens is not None else settings.max_tokens
            
            logger.debug(f"LLM request to {self.model}")
            
            response = await litellm.acompletion(
                model=self.model,
                messages=messages,
                temperature=temp,
                max_tokens=tokens,
            )
            
            content = response.choices[0].message.content
            
            # Log the request
            log_llm_request(
                provider=self.provider,
                model=self.model,
                tokens=response.usage.total_tokens if hasattr(response, 'usage') else 0
            )
            
            return content
            
        except litellm.RateLimitError as e:
            logger.error(f"Rate limit exceeded for {self.provider}")
            raise LLMRateLimitError(self.provider) from e
            
        except litellm.AuthenticationError as e:
            logger.error(f"Authentication failed for {self.provider}")
            raise LLMAPIKeyMissingError(self.provider) from e
            
        except Exception as e:
            logger.error(f"LLM request failed: {e}")
            raise LLMProviderError(self.provider, str(e)) from e
    
    async def complete_structured(
        self,
        messages: list[dict[str, str]],
        response_model: type[BaseModel],
        temperature: float | None = None,
    ) -> BaseModel:
        """
        Generate a structured response matching a Pydantic model.
        
        Uses function calling or JSON mode depending on provider support.
        
        Args:
            messages: List of message dicts
            response_model: Pydantic model class
            temperature: Sampling temperature
            
        Returns:
            Instance of response_model
        """
        try:
            temp = temperature if temperature is not None else settings.temperature
            
            # Add schema instruction to system message
            schema_instruction = f"\n\nRespond with a JSON object matching this schema: {response_model.model_json_schema()}"
            
            # Add to last user message or create system message
            enhanced_messages = messages.copy()
            if enhanced_messages and enhanced_messages[0]["role"] == "system":
                enhanced_messages[0]["content"] += schema_instruction
            else:
                enhanced_messages.insert(0, {
                    "role": "system",
                    "content": f"You are a helpful assistant.{schema_instruction}"
                })
            
            # Request with JSON mode if supported
            response = await litellm.acompletion(
                model=self.model,
                messages=enhanced_messages,
                temperature=temp,
                response_format={"type": "json_object"} if self._supports_json_mode() else None,
            )
            
            content = response.choices[0].message.content
            
            # Parse JSON into Pydantic model
            import json
            data = json.loads(content)
            return response_model.model_validate(data)
            
        except Exception as e:
            logger.error(f"Structured completion failed: {e}")
            raise LLMProviderError(self.provider, str(e)) from e
    
    def _supports_json_mode(self) -> bool:
        """Check if the current model supports JSON mode."""
        json_mode_models = [
            "gpt-4",
            "gpt-3.5",
            "gemini",
        ]
        return any(model in self.model for model in json_mode_models)
