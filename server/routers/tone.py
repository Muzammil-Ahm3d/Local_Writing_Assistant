"""
Tone Analysis Router

Handles /api/tone endpoint for sentiment and formality analysis.
Uses heuristic-based analysis for completely offline operation.
"""

import time
import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from server.services.tone import ToneAnalysisService, ToneAnalysis, Sentiment, Formality

logger = logging.getLogger(__name__)

router = APIRouter()

class ToneRequest(BaseModel):
    """Request model for tone analysis"""
    text: str = Field(..., min_length=1, max_length=5000, description="Text to analyze (max 5,000 characters)")

class ToneLabels(BaseModel):
    """Tone labels response model"""
    sentiment: str = Field(..., description="Sentiment: positive, neutral, or negative")
    formality: str = Field(..., description="Formality: formal, neutral, or casual")

class ToneResponse(BaseModel):
    """Response model for tone analysis"""
    labels: ToneLabels = Field(..., description="Detected tone labels")
    scores: Dict[str, float] = Field(default={}, description="Numerical scores for each dimension")
    confidence: float = Field(..., description="Confidence in the analysis (0.0 to 1.0)")
    time_ms: int = Field(..., description="Processing time in milliseconds")
    text_length: int = Field(..., description="Length of analyzed text")

class DetailedToneResponse(BaseModel):
    """Detailed response model for tone analysis"""
    labels: ToneLabels = Field(..., description="Detected tone labels")
    scores: Dict[str, float] = Field(default={}, description="Numerical scores for each dimension")
    confidence: float = Field(..., description="Confidence in the analysis (0.0 to 1.0)")
    features: Dict[str, Any] = Field(default={}, description="Extracted linguistic features")
    time_ms: int = Field(..., description="Processing time in milliseconds")
    text_length: int = Field(..., description="Length of analyzed text")

class BatchToneRequest(BaseModel):
    """Request model for batch tone analysis"""
    texts: list[str] = Field(..., max_items=10, description="List of texts to analyze (max 10)")

# Global tone analysis service instance
_tone_service = None

def get_tone_service() -> ToneAnalysisService:
    """Get the tone analysis service instance"""
    global _tone_service
    if _tone_service is None:
        _tone_service = ToneAnalysisService()
    return _tone_service

@router.post("/tone", response_model=ToneResponse)
async def analyze_tone(
    request: ToneRequest,
    tone_service: ToneAnalysisService = Depends(get_tone_service)
) -> ToneResponse:
    """
    Analyze the tone of text
    
    Provides sentiment (positive/neutral/negative) and formality (formal/neutral/casual)
    analysis using heuristic methods. Completely offline with no external dependencies.
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
        logger.debug(f"Analyzing tone for text: {text_preview}")
        
        # Perform tone analysis
        analysis = tone_service.analyze_tone(request.text)
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        logger.info(f"Tone analysis completed in {processing_time_ms}ms: sentiment={analysis.sentiment.value}, formality={analysis.formality.value}")
        
        return ToneResponse(
            labels=ToneLabels(
                sentiment=analysis.sentiment.value,
                formality=analysis.formality.value
            ),
            scores=analysis.scores,
            confidence=analysis.confidence,
            time_ms=processing_time_ms,
            text_length=len(request.text)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time_ms = int((time.time() - start_time) * 1000)
        logger.error(f"Tone analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Tone analysis failed: {str(e)}"
        )

@router.post("/tone/detailed", response_model=DetailedToneResponse)
async def analyze_tone_detailed(
    request: ToneRequest,
    tone_service: ToneAnalysisService = Depends(get_tone_service)
) -> DetailedToneResponse:
    """
    Analyze the tone of text with detailed features
    
    Returns the same tone analysis as /tone but includes detailed linguistic features
    that were used in the analysis. Useful for debugging and understanding results.
    """
    start_time = time.time()
    
    try:
        # Validate input
        if not request.text.strip():
            raise HTTPException(
                status_code=400,
                detail="Text cannot be empty"
            )
        
        # Perform tone analysis
        analysis = tone_service.analyze_tone(request.text)
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        logger.info(f"Detailed tone analysis completed in {processing_time_ms}ms")
        
        return DetailedToneResponse(
            labels=ToneLabels(
                sentiment=analysis.sentiment.value,
                formality=analysis.formality.value
            ),
            scores=analysis.scores,
            confidence=analysis.confidence,
            features=analysis.features,
            time_ms=processing_time_ms,
            text_length=len(request.text)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time_ms = int((time.time() - start_time) * 1000)
        logger.error(f"Detailed tone analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Detailed tone analysis failed: {str(e)}"
        )

@router.post("/tone/batch")
async def analyze_tone_batch(
    request: BatchToneRequest,
    tone_service: ToneAnalysisService = Depends(get_tone_service)
) -> dict:
    """
    Analyze the tone of multiple texts
    
    Useful for batch processing multiple sentences or paragraphs.
    Limited to 10 texts per request to prevent overload.
    """
    start_time = time.time()
    
    try:
        if not request.texts:
            raise HTTPException(
                status_code=400,
                detail="No texts provided"
            )
        
        if len(request.texts) > 10:
            raise HTTPException(
                status_code=400,
                detail="Too many texts. Maximum 10 texts per batch request."
            )
        
        results = []
        total_confidence = 0.0
        processed_count = 0
        
        for i, text in enumerate(request.texts):
            if not text.strip():
                logger.warning(f"Skipping empty text at index {i}")
                results.append({
                    "text": text,
                    "labels": {"sentiment": "neutral", "formality": "neutral"},
                    "scores": {"sentiment": 0.0, "formality": 0.0},
                    "confidence": 0.0,
                    "skipped": True,
                    "reason": "Empty text"
                })
                continue
            
            try:
                analysis = tone_service.analyze_tone(text)
                results.append({
                    "text": text,
                    "labels": {
                        "sentiment": analysis.sentiment.value,
                        "formality": analysis.formality.value
                    },
                    "scores": analysis.scores,
                    "confidence": analysis.confidence,
                    "skipped": False
                })
                
                total_confidence += analysis.confidence
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Failed to analyze text {i}: {e}")
                results.append({
                    "text": text,
                    "labels": {"sentiment": "neutral", "formality": "neutral"},
                    "scores": {"sentiment": 0.0, "formality": 0.0},
                    "confidence": 0.0,
                    "skipped": True,
                    "reason": f"Analysis failed: {str(e)}"
                })
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        avg_confidence = total_confidence / max(processed_count, 1)
        
        return {
            "results": results,
            "time_ms": processing_time_ms,
            "total_texts": len(request.texts),
            "successful_analyses": processed_count,
            "average_confidence": avg_confidence
        }
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time_ms = int((time.time() - start_time) * 1000)
        logger.error(f"Batch tone analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Batch tone analysis failed: {str(e)}"
        )

@router.get("/tone/info")
async def get_tone_info() -> dict:
    """Get information about tone analysis capabilities"""
    return {
        "description": "Heuristic-based tone analysis service",
        "dimensions": {
            "sentiment": {
                "description": "Emotional polarity of the text",
                "values": ["positive", "neutral", "negative"],
                "methods": ["word sentiment", "punctuation", "emoticons", "capitalization"]
            },
            "formality": {
                "description": "Level of formality in the text",
                "values": ["formal", "neutral", "casual"],
                "methods": ["vocabulary choice", "contractions", "sentence structure", "word length"]
            }
        },
        "features": [
            "Word count and ratios",
            "Punctuation analysis",
            "Contraction detection",
            "Vocabulary formality scoring",
            "Sentence structure analysis"
        ],
        "offline": True,
        "privacy": "All analysis is performed locally with no external requests"
    }
