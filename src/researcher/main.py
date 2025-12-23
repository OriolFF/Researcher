"""
FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from pathlib import Path

from researcher.api.routes import router
from researcher.core.config import settings
from researcher.core.logging import logger, setup_logging

# Initialize logging
setup_logging()

# Create FastAPI app
app = FastAPI(
    title="Historical Researcher API",
    description="AI-powered research assistant for historically accurate storytelling",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="", tags=["research"])

# Serve web client static files
web_dir = Path(__file__).parent.parent.parent.parent / "web"
if web_dir.exists():
    app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")
    
    @app.get("/")
    async def serve_web_client():
        """Serve the web client HTML."""
        return FileResponse(str(web_dir / "index.html"))

logger.info(
    f"FastAPI app initialized: {settings.llm_provider.value}:{settings.llm_model}"
)


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info("Application starting up...")
    logger.info(f"Tier 1 enabled: {settings.tier1_enabled}")
    logger.info(f"Tier 2 available: {settings.is_tier2_available()}")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info("Application shutting down...")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "researcher.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
    )
