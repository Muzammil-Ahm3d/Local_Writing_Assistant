"""
OpenAI-Based Text Rewriter Service

Provides AI-powered text rewriting using OpenAI's GPT-4 mini model.
Offers multiple rewriting modes for different use cases.
"""

import os
import logging
from typing import Dict, List, Tuple, Optional
from enum import Enum

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class RewriteMode(str, Enum):
    """Available rewriting modes"""
    FIX = "fix"
    CONCISE = "concise"
    FORMAL = "formal"
    FRIENDLY = "friendly"
    ELABORATE = "elaborate"
    CREATIVE = "creative"


class OpenAIRewriterService:
    """OpenAI-based text rewriter service"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = None
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("OPENAI_BASE_URL")
        self.initialized = False
        
        if not OPENAI_AVAILABLE:
            self.logger.warning("OpenAI library not installed. Run: pip install openai")
        elif not self.api_key or self.api_key == "your-openai-api-key-here":
            self.logger.warning("OpenAI API key not configured. Add OPENAI_API_KEY to .env file")
        else:
            self.logger.info(f"Attempting to initialize OpenAI with key: {self.api_key[:10]}...")
            self._initialize()
    
    def _initialize(self):
        """Initialize OpenAI client"""
        try:
            from openai import OpenAI
            # Use custom base URL if provided
            if self.base_url:
                self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
                self.logger.info(f"OpenAI service initialized with custom endpoint: {self.base_url}")
            else:
                self.client = OpenAI(api_key=self.api_key)
            self.initialized = True
            self.logger.info(f"OpenAI service initialized with model: {self.model}")
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI client: {e}")
            self.initialized = False
    
    def _get_system_prompt(self, mode: RewriteMode) -> str:
        """Get the appropriate system prompt for the rewriting mode"""
        prompts = {
            RewriteMode.FIX: """You are a grammar and spelling correction assistant. 
Fix any grammatical errors, spelling mistakes, and punctuation issues in the text.
Maintain the original tone and meaning. Only make necessary corrections.""",
            
            RewriteMode.CONCISE: """You are a concise writing assistant.
Make the text more concise and to the point. Remove unnecessary words and phrases.
Maintain the core message but express it more efficiently.""",
            
            RewriteMode.FORMAL: """You are a formal writing assistant.
Rewrite the text in a professional, formal tone suitable for business communication.
Use proper grammar and vocabulary while maintaining the original meaning.""",
            
            RewriteMode.FRIENDLY: """You are a friendly writing assistant.
Rewrite the text in a warm, conversational, and approachable tone.
Make it sound natural and engaging while keeping the core message.""",
            
            RewriteMode.ELABORATE: """You are a detailed writing assistant.
Expand on the text to make it more comprehensive and detailed.
Add relevant context and explanations while maintaining clarity.""",
            
            RewriteMode.CREATIVE: """You are a creative writing assistant.
Rewrite the text in a more creative and engaging way.
Use vivid language and interesting phrasing while preserving the meaning."""
        }
        
        return prompts.get(mode, prompts[RewriteMode.FIX])
    
    async def rewrite_text(self, text: str, mode: RewriteMode) -> str:
        """
        Rewrite text using OpenAI GPT model
        
        Args:
            text: Input text to rewrite
            mode: Rewriting mode
            
        Returns:
            Rewritten text
        """
        if not self.initialized:
            self.logger.warning("OpenAI service not initialized, falling back to original text")
            return text
        
        if not text or not text.strip():
            return text
        
        original_text = text.strip()
        self.logger.debug(f"Rewriting with OpenAI mode '{mode}': {original_text[:50]}...")
        
        try:
            # Prepare the messages
            messages = [
                {"role": "system", "content": self._get_system_prompt(mode)},
                {"role": "user", "content": f"Rewrite the following text:\n\n{original_text}"}
            ]
            
            # Call OpenAI API with optimized settings for speed
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=min(len(original_text) * 2, 500),  # Reduced for faster responses
                temperature=0.7 if mode in [RewriteMode.CREATIVE, RewriteMode.FRIENDLY] else 0.3,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1,
                stream=False  # Ensure streaming is off
            )
            
            # Extract the rewritten text
            result = response.choices[0].message.content.strip()
            
            if not result:
                result = original_text  # Fallback to original if empty
            
            self.logger.debug(f"OpenAI rewrite successful")
            return result
            
        except Exception as e:
            self.logger.error(f"OpenAI API error: {e}")
            return original_text  # Return original on error
    
    async def health_check(self) -> Tuple[bool, Dict[str, any]]:
        """
        Check if the OpenAI rewriter service is healthy
        
        Returns:
            Tuple of (is_healthy: bool, details: dict)
        """
        try:
            if not OPENAI_AVAILABLE:
                return False, {
                    "service": "OpenAIRewriter",
                    "status": "unavailable",
                    "error": "OpenAI library not installed"
                }
            
            if not self.initialized:
                return False, {
                    "service": "OpenAIRewriter",
                    "status": "not_configured",
                    "error": "OpenAI API key not configured"
                }
            
            # Test with a simple request
            test_text = "hello world"
            result = await self.rewrite_text(test_text, RewriteMode.FIX)
            
            return True, {
                "service": "OpenAIRewriter",
                "status": "healthy",
                "model": self.model,
                "modes_available": [mode.value for mode in RewriteMode],
                "test_successful": bool(result)
            }
            
        except Exception as e:
            return False, {
                "service": "OpenAIRewriter",
                "status": "unhealthy",
                "error": str(e)
            }
