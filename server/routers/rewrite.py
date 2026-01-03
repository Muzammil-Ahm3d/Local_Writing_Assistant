"""
Text Rewrite Router

Handles /api/rewrite endpoint for text rewriting using Flan-T5-small.
Supports different rewriting modes: fix, concise, formal, friendly.
"""

import time
import logging
from typing import Dict

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from server.services.fast_rewriter import FastRewriterService, RewriteMode
from server.services.openai_rewriter import OpenAIRewriterService
from server.services.openai_rewriter import RewriteMode as OpenAIRewriteMode

logger = logging.getLogger(__name__)

router = APIRouter()

class RewriteRequest(BaseModel):
    """Request model for text rewriting"""
    text: str = Field(..., min_length=1, max_length=2000, description="Text to rewrite (max 2,000 characters)")
    mode: RewriteMode = Field(..., description="Rewriting mode: fix, concise, formal, friendly")

class RewriteResponse(BaseModel):
    """Response model for text rewriting"""
    text: str = Field(..., description="Rewritten text")
    time_ms: int = Field(..., description="Processing time in milliseconds")
    mode_used: str = Field(..., description="Rewriting mode that was used")
    original_length: int = Field(..., description="Length of original text")
    rewritten_length: int = Field(..., description="Length of rewritten text")

class BatchRewriteRequest(BaseModel):
    """Request model for batch rewriting"""
    texts: list[str] = Field(..., max_items=5, description="List of texts to rewrite (max 5)")
    mode: RewriteMode = Field(..., description="Rewriting mode to apply to all texts")

# Global fast rewriter service instance
_rewriter_service = None

def get_rewriter_service():
    """Get the rewriter service instance (OpenAI if available, else fast rewriter)"""
    # This will be injected by the main app
    from server.main import openai_rewriter_service, fast_rewriter_service
    
    # Use OpenAI service if it's initialized, otherwise fall back to fast rewriter
    if openai_rewriter_service and openai_rewriter_service.initialized:
        logger.info("Using OpenAI rewriter service")
        return openai_rewriter_service
    else:
        logger.info("Using fast rewriter service")
        return fast_rewriter_service

@router.post("/rewrite", response_model=RewriteResponse)
async def rewrite_text(
    request: RewriteRequest,
    rewriter = Depends(get_rewriter_service)
) -> RewriteResponse:
    """
    Rewrite text using AI-powered transformation (OpenAI if available)
    
    This endpoint uses either OpenAI GPT-4 mini or rule-based transformations to rewrite
    text according to the specified mode. AI service provides more intelligent rewrites.
    """
    start_time = time.time()
    
    try:
        # Validate input
        if not request.text.strip():
            raise HTTPException(
                status_code=400,
                detail="Text cannot be empty"
            )
        
        # Log the request (without full text for privacy)
        text_preview = request.text[:50] + "..." if len(request.text) > 50 else request.text
        logger.info(f"Rewriting text with mode '{request.mode}': {text_preview}")
        
        # Perform the rewrite
        rewritten_text = await rewriter.rewrite_text(request.text, request.mode)
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Validate output
        if not rewritten_text:
            logger.warning("Rewriter returned empty result")
            rewritten_text = request.text  # Fallback to original text
        
        logger.info(f"Rewrite completed in {processing_time_ms}ms")
        
        return RewriteResponse(
            text=rewritten_text,
            time_ms=processing_time_ms,
            mode_used=request.mode.value,
            original_length=len(request.text),
            rewritten_length=len(rewritten_text)
        )
        
    except ValueError as e:
        processing_time_ms = int((time.time() - start_time) * 1000)
        logger.error(f"Invalid rewrite request: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except RuntimeError as e:
        processing_time_ms = int((time.time() - start_time) * 1000)
        logger.error(f"Rewriter service error: {e}")
        
        if "dependencies" in str(e).lower():
            raise HTTPException(
                status_code=503,
                detail="Text rewriting service unavailable: Required AI models not installed. Please run the setup script."
            )
        else:
            raise HTTPException(
                status_code=503,
                detail="Text rewriting service temporarily unavailable. Please try again later."
            )
    except Exception as e:
        processing_time_ms = int((time.time() - start_time) * 1000)
        logger.error(f"Rewrite failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Text rewriting failed: {str(e)}"
        )

@router.get("/rewrite/modes")
async def get_rewrite_modes(
    rewriter = Depends(get_rewriter_service)
) -> Dict[str, str]:
    """Get available rewriting modes with descriptions"""
    try:
        modes = {mode.value: mode.value.replace('_', ' ').title() for mode in RewriteMode}
        return {
            "modes": modes,
            "default": "fix",
            "message": "Available rewriting modes (fast rule-based)"
        }
    except Exception as e:
        logger.error(f"Failed to get rewrite modes: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve rewriting modes"
        )

@router.post("/rewrite/batch")
async def rewrite_batch(
    request: BatchRewriteRequest,
    rewriter = Depends(get_rewriter_service)
) -> dict:
    """
    Rewrite multiple texts using the same mode
    
    Useful for batch processing multiple sentences or paragraphs.
    Limited to 5 texts per request to prevent overload.
    """
    start_time = time.time()
    
    try:
        if not request.texts:
            raise HTTPException(
                status_code=400,
                detail="No texts provided"
            )
        
        if len(request.texts) > 5:
            raise HTTPException(
                status_code=400,
                detail="Too many texts. Maximum 5 texts per batch request."
            )
        
        results = []
        total_original_length = 0
        total_rewritten_length = 0
        
        for i, text in enumerate(request.texts):
            if not text.strip():
                logger.warning(f"Skipping empty text at index {i}")
                results.append({
                    "original": text,
                    "rewritten": text,
                    "skipped": True,
                    "reason": "Empty text"
                })
                continue
            
            try:
                rewritten = await rewriter.rewrite_text(text, request.mode)
                results.append({
                    "original": text,
                    "rewritten": rewritten,
                    "skipped": False
                })
                
                total_original_length += len(text)
                total_rewritten_length += len(rewritten)
                
            except Exception as e:
                logger.error(f"Failed to rewrite text {i}: {e}")
                results.append({
                    "original": text,
                    "rewritten": text,  # Fallback to original
                    "skipped": True,
                    "reason": f"Rewrite failed: {str(e)}"
                })
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return {
            "results": results,
            "time_ms": processing_time_ms,
            "mode_used": request.mode.value,
            "total_texts": len(request.texts),
            "successful_rewrites": len([r for r in results if not r.get("skipped", False)]),
            "total_original_length": total_original_length,
            "total_rewritten_length": total_rewritten_length
        }
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time_ms = int((time.time() - start_time) * 1000)
        logger.error(f"Batch rewrite failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Batch rewriting failed: {str(e)}"
        )
