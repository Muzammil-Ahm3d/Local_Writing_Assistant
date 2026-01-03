"""
Grammar Check Router

Handles /api/check endpoint for real-time grammar, style, and spelling checking.
"""

import time
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from server.services.languagetool import LanguageToolService, GrammarIssue

logger = logging.getLogger(__name__)

router = APIRouter()

class CheckRequest(BaseModel):
    """Request model for grammar checking"""
    text: str = Field(..., max_length=10000, description="Text to check (max 10,000 characters)")
    language: str = Field(default="en-US", description="Language code (e.g., en-US, en-GB)")

class IssueResponse(BaseModel):
    """Response model for a single grammar issue"""
    start: int = Field(..., description="Start position of the issue in the text")
    end: int = Field(..., description="End position of the issue in the text")
    message: str = Field(..., description="Description of the issue")
    replacements: List[str] = Field(default=[], description="Suggested replacements")
    rule_id: str = Field(..., description="Rule identifier")
    category: Optional[str] = Field(None, description="Issue category")

class CheckResponse(BaseModel):
    """Response model for grammar checking"""
    issues: List[IssueResponse] = Field(default=[], description="List of found issues")
    time_ms: int = Field(..., description="Processing time in milliseconds")
    language_used: str = Field(..., description="Language used for checking")
    text_length: int = Field(..., description="Length of checked text")

# Dependency to get LanguageTool service
def get_languagetool_service() -> LanguageToolService:
    """Get the LanguageTool service instance"""
    # This will be injected by the main app
    from server.main import lt_service
    if not lt_service:
        raise HTTPException(
            status_code=503,
            detail="LanguageTool service not available. Please check if Java is installed and the service is running."
        )
    return lt_service

@router.post("/check", response_model=CheckResponse)
async def check_grammar(
    request: CheckRequest,
    lt_service: LanguageToolService = Depends(get_languagetool_service)
) -> CheckResponse:
    """
    Check text for grammar, style, and spelling issues
    
    This endpoint provides real-time grammar checking with debouncing support.
    Optimized for checking individual sentences or short paragraphs.
    """
    start_time = time.time()
    
    try:
        # Validate input
        if not request.text.strip():
            return CheckResponse(
                issues=[],
                time_ms=int((time.time() - start_time) * 1000),
                language_used=request.language,
                text_length=0
            )
        
        # Validate language code
        supported_languages = await lt_service.get_languages()
        if request.language not in supported_languages:
            logger.warning(f"Unsupported language '{request.language}', falling back to en-US")
            language_to_use = "en-US"
        else:
            language_to_use = request.language
        
        logger.debug(f"Checking text of length {len(request.text)} in language {language_to_use}")
        
        # Check for issues
        issues = await lt_service.check_text(request.text, language_to_use)
        
        # Convert to response format
        issue_responses = []
        for issue in issues:
            issue_response = IssueResponse(
                start=issue.start,
                end=issue.end,
                message=issue.message,
                replacements=issue.replacements,
                rule_id=issue.rule_id,
                category=issue.category
            )
            issue_responses.append(issue_response)
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        logger.info(f"Found {len(issue_responses)} issues in {processing_time_ms}ms")
        
        return CheckResponse(
            issues=issue_responses,
            time_ms=processing_time_ms,
            language_used=language_to_use,
            text_length=len(request.text)
        )
        
    except Exception as e:
        processing_time_ms = int((time.time() - start_time) * 1000)
        logger.error(f"Grammar check failed: {e}")
        
        # Return appropriate error based on the exception type
        if "Java" in str(e):
            raise HTTPException(
                status_code=503,
                detail="Grammar checking service unavailable: Java runtime not found. Please install Java JDK 17+."
            )
        elif "LanguageTool" in str(e):
            raise HTTPException(
                status_code=503,
                detail="Grammar checking service temporarily unavailable. Please try again later."
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Grammar check failed: {str(e)}"
            )

@router.post("/check/sentence", response_model=CheckResponse)
async def check_sentence(
    request: CheckRequest,
    lt_service: LanguageToolService = Depends(get_languagetool_service)
) -> CheckResponse:
    """
    Check a single sentence for issues
    
    Optimized endpoint for real-time checking with debouncing.
    Should be used for checking individual sentences as the user types.
    """
    start_time = time.time()
    
    try:
        # Use the optimized sentence checking method
        issues = await lt_service.check_sentence(request.text, request.language)
        
        # Convert to response format
        issue_responses = []
        for issue in issues:
            issue_response = IssueResponse(
                start=issue.start,
                end=issue.end,
                message=issue.message,
                replacements=issue.replacements,
                rule_id=issue.rule_id,
                category=issue.category
            )
            issue_responses.append(issue_response)
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return CheckResponse(
            issues=issue_responses,
            time_ms=processing_time_ms,
            language_used=request.language,
            text_length=len(request.text)
        )
        
    except Exception as e:
        processing_time_ms = int((time.time() - start_time) * 1000)
        logger.error(f"Sentence check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Sentence check failed: {str(e)}"
        )

@router.get("/check/languages")
async def get_supported_languages(
    lt_service: LanguageToolService = Depends(get_languagetool_service)
) -> dict:
    """Get list of supported languages for grammar checking"""
    try:
        languages = await lt_service.get_languages()
        return {
            "languages": languages,
            "default": "en-US",
            "message": "Supported languages for grammar checking"
        }
    except Exception as e:
        logger.error(f"Failed to get supported languages: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve supported languages"
        )
