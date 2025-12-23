"""
Centralized logging configuration using Loguru.

Provides structured logging with tier tracking, performance metrics, and configurable output formats.
"""

import sys
from pathlib import Path

from loguru import logger

from researcher.core.config import settings


def setup_logging() -> None:
    """
    Configure loguru logger based on settings.
    
    Features:
    - Structured logging with JSON or text format
    - Tier tracking (Tier 1 vs Tier 2 usage)
    - Performance metrics logging
    - Configurable log levels
    """
    # Remove default handler
    logger.remove()
    
    # Determine format
    if settings.log_format == "json":
        log_format = (
            "{{"
            '"timestamp":"{time:YYYY-MM-DD HH:mm:ss.SSS}",'
            '"level":"{level}",'
            '"module":"{name}",'
            '"function":"{function}",'
            '"line":{line},'
            '"message":"{message}"'
            "}}"
        )
    else:
        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
    
    # Add console handler
    logger.add(
        sys.stdout,
        format=log_format,
        level=settings.log_level,
        colorize=settings.log_format == "text",
        backtrace=True,
        diagnose=True,
    )
    
    # Add file handler for production
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logger.add(
        log_dir / "researcher_{time:YYYY-MM-DD}.log",
        format=log_format,
        level=settings.log_level,
        rotation="00:00",  # Rotate daily
        retention="30 days",
        compression="zip",
    )
    
    logger.info(
        f"Logging initialized: level={settings.log_level}, format={settings.log_format}"
    )


def log_research_request(query: str, depth: str, tier: str) -> None:
    """Log a research request."""
    logger.info(
        f"Research request received",
        extra={
            "query_length": len(query),
            "depth": depth,
            "tier": tier,
        }
    )


def log_tier_escalation(reason: str, from_tier: str, to_tier: str) -> None:
    """Log tier escalation event."""
    logger.warning(
        f"Escalating from {from_tier} to {to_tier}",
        extra={
            "reason": reason,
            "from_tier": from_tier,
            "to_tier": to_tier,
        }
    )


def log_research_result(
    tier_used: str,
    source_count: int,
    confidence: float,
    execution_time_ms: float
) -> None:
    """Log research result metrics."""
    logger.info(
        f"Research completed",
        extra={
            "tier_used": tier_used,
            "source_count": source_count,
            "confidence": confidence,
            "execution_time_ms": execution_time_ms,
        }
    )


def log_llm_request(provider: str, model: str, tokens: int) -> None:
    """Log LLM API request."""
    logger.debug(
        f"LLM request",
        extra={
            "provider": provider,
            "model": model,
            "tokens": tokens,
        }
    )


def log_error(error: Exception, context: dict | None = None) -> None:
    """Log error with context."""
    logger.error(
        f"Error occurred: {type(error).__name__}: {str(error)}",
        extra=context or {}
    )

