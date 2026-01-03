"""
Local Writing Assistant - FastAPI Backend
Privacy-first, offline grammar and writing assistance.
"""
import os
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from pydantic import BaseModel

from server.routers import check, rewrite, tone, transcribe
from server.services.languagetool import LanguageToolService
from server.services.fast_rewriter import FastRewriterService
from server.services.openai_rewriter import OpenAIRewriterService
from server.services.browser_speech import BrowserSpeechService

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global services
lt_service: Optional[LanguageToolService] = None
fast_rewriter_service: Optional[FastRewriterService] = None
openai_rewriter_service: Optional[OpenAIRewriterService] = None
browser_speech_service: Optional[BrowserSpeechService] = None

security = HTTPBearer(auto_error=False)

class HealthResponse(BaseModel):
    ok: bool
    message: str = "Service is healthy"
    version: str = "1.0.0"

class ServiceHealthResponse(BaseModel):
    ok: bool
    service: str
    message: str
    details: Optional[dict] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup services"""
    global lt_service, fast_rewriter_service, openai_rewriter_service, browser_speech_service
    
    logger.info("Starting Local Writing Assistant...")
    
    # Initialize LanguageTool service
    try:
        lt_service = LanguageToolService()
        await lt_service.initialize()
        logger.info("LanguageTool service initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize LanguageTool: {e}")
    
    # Initialize OpenAI Rewriter service if API key is available
    openai_rewriter_service = OpenAIRewriterService()
    if openai_rewriter_service.initialized:
        logger.info("OpenAI Rewriter service initialized successfully")
    else:
        logger.warning("OpenAI Rewriter service not available, using Fast Rewriter as fallback")
    
    # Initialize Fast Rewriter service (fallback)
    fast_rewriter_service = FastRewriterService()
    logger.info("Fast Rewriter service initialized")
    
    # Initialize Browser Speech service (instant)
    browser_speech_service = BrowserSpeechService()
    logger.info("Browser Speech service initialized")
    
    logger.info("Local Writing Assistant started successfully")
    
    yield
    
    # Cleanup
    logger.info("Shutting down Local Writing Assistant...")
    if lt_service:
        await lt_service.cleanup()
    # Fast services don't need cleanup
    logger.info("Local Writing Assistant stopped")

# Create FastAPI app
app = FastAPI(
    title="Local Writing Assistant",
    description="Privacy-first, offline grammar and writing assistance",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration for Chrome extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Authentication dependency
async def verify_token(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> None:
    """Verify API token for protected endpoints"""
    # Skip auth for health endpoints and OPTIONS requests
    if request.url.path.startswith("/health") or request.method == "OPTIONS":
        return
    
    expected_token = os.getenv("LOCAL_API_TOKEN")
    if not expected_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error: API token not set"
        )
    
    # Check X-Local-Auth header
    auth_header = request.headers.get("X-Local-Auth")
    if auth_header and auth_header == expected_token:
        return
    
    # Check Authorization header
    if credentials and credentials.credentials == expected_token:
        return
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing authentication token",
        headers={"WWW-Authenticate": "Bearer"}
    )

# Health endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Basic health check"""
    return HealthResponse(ok=True)

@app.get("/health/lt", response_model=ServiceHealthResponse)
async def health_check_languagetool():
    """LanguageTool service health check"""
    if not lt_service:
        return ServiceHealthResponse(
            ok=False,
            service="LanguageTool",
            message="Service not initialized"
        )
    
    try:
        is_healthy, details = await lt_service.health_check()
        return ServiceHealthResponse(
            ok=is_healthy,
            service="LanguageTool",
            message="Service is healthy" if is_healthy else "Service is unhealthy",
            details=details
        )
    except Exception as e:
        return ServiceHealthResponse(
            ok=False,
            service="LanguageTool",
            message=f"Health check failed: {str(e)}"
        )

@app.get("/health/rewriter", response_model=ServiceHealthResponse)
async def health_check_rewriter():
    """Fast Rewriter service health check"""
    if not fast_rewriter_service:
        return ServiceHealthResponse(
            ok=False,
            service="FastRewriter",
            message="Service not initialized"
        )
    
    try:
        is_healthy, details = await fast_rewriter_service.health_check()
        return ServiceHealthResponse(
            ok=is_healthy,
            service="FastRewriter",
            message="Service is healthy" if is_healthy else "Service is unhealthy",
            details=details
        )
    except Exception as e:
        return ServiceHealthResponse(
            ok=False,
            service="FastRewriter",
            message=f"Health check failed: {str(e)}"
        )

@app.get("/health/speech", response_model=ServiceHealthResponse)
async def health_check_speech():
    """Browser Speech service health check"""
    if not browser_speech_service:
        return ServiceHealthResponse(
            ok=False,
            service="BrowserSpeech",
            message="Service not initialized"
        )
    
    try:
        is_healthy, details = await browser_speech_service.health_check()
        return ServiceHealthResponse(
            ok=is_healthy,
            service="BrowserSpeech",
            message="Service is healthy" if is_healthy else "Service is unhealthy",
            details=details
        )
    except Exception as e:
        return ServiceHealthResponse(
            ok=False,
            service="BrowserSpeech",
            message=f"Health check failed: {str(e)}"
        )

@app.get("/health/openai", response_model=ServiceHealthResponse)
async def health_check_openai():
    """OpenAI Rewriter service health check"""
    if not openai_rewriter_service:
        return ServiceHealthResponse(
            ok=False,
            service="OpenAIRewriter",
            message="Service not initialized"
        )
    
    try:
        is_healthy, details = await openai_rewriter_service.health_check()
        return ServiceHealthResponse(
            ok=is_healthy,
            service="OpenAIRewriter",
            message="Service is healthy" if is_healthy else "Service is unhealthy",
            details=details
        )
    except Exception as e:
        return ServiceHealthResponse(
            ok=False,
            service="OpenAIRewriter",
            message=f"Health check failed: {str(e)}"
        )

# API Documentation endpoint
@app.get("/docs-info")
async def docs_info():
    """Information about API documentation"""
    return {
        "message": "Local Writing Assistant API",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "privacy": "All processing is done locally. No data is sent to external servers.",
        "auth": "Include X-Local-Auth header with your token for API access"
    }

# Include routers with authentication
app.include_router(
    check.router,
    prefix="/api",
    dependencies=[Depends(verify_token)],
    tags=["Grammar Check"]
)

app.include_router(
    rewrite.router,
    prefix="/api",
    dependencies=[Depends(verify_token)],
    tags=["Text Rewrite"]
)

app.include_router(
    tone.router,
    prefix="/api",
    dependencies=[Depends(verify_token)],
    tags=["Tone Analysis"]
)

app.include_router(
    transcribe.router,
    prefix="/api",
    dependencies=[Depends(verify_token)],
    tags=["Voice Transcription"]
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please check the server logs.",
            "type": type(exc).__name__
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("SERVER_HOST", "127.0.0.1")
    port = int(os.getenv("SERVER_PORT", "8001"))
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
