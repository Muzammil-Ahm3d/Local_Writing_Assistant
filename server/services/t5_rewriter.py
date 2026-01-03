"""
T5 Rewriter Service for Local Writing Assistant

Provides text rewriting capabilities using Google's Flan-T5-small model.
Supports different rewriting modes: fix, concise, formal, friendly.
Optimized for CPU-only inference with lazy loading.
"""

import os
import asyncio
import logging
from typing import Dict, Any, Tuple, Optional
from pathlib import Path
from enum import Enum

class RewriteMode(str, Enum):
    """Available rewriting modes"""
    FIX = "fix"
    CONCISE = "concise"
    FORMAL = "formal" 
    FRIENDLY = "friendly"

class T5RewriterService:
    """Service for text rewriting using Flan-T5-small"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._tokenizer = None
        self._model = None
        self._is_loaded = False
        self._models_dir = Path(__file__).parent.parent / "models"
        
        # Rewrite prompts for different modes
        self._prompts = {
            RewriteMode.FIX: "Correct the grammar and spelling: {text}",
            RewriteMode.CONCISE: "Rewrite this more concisely: {text}",
            RewriteMode.FORMAL: "Rewrite this in a formal tone: {text}",
            RewriteMode.FRIENDLY: "Rewrite this in a friendly tone: {text}"
        }
    
    async def _load_model(self) -> None:
        """Lazy load the Flan-T5 model and tokenizer"""
        if self._is_loaded:
            return
        
        self.logger.info("Loading Flan-T5-small model...")
        
        try:
            # Import here to avoid loading dependencies until needed
            from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
            import torch
            
            # Check if local model exists
            local_model_path = self._models_dir / "flan-t5-small" / "local_model"
            
            if local_model_path.exists():
                model_path = str(local_model_path)
                self.logger.info(f"Loading model from local cache: {model_path}")
            else:
                model_path = "google/flan-t5-small"
                self.logger.info(f"Loading model from HuggingFace: {model_path}")
            
            # Load in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            
            # Load tokenizer
            self._tokenizer = await loop.run_in_executor(
                None,
                lambda: AutoTokenizer.from_pretrained(
                    model_path,
                    cache_dir=str(self._models_dir / "flan-t5-small")
                )
            )
            
            # Load model with CPU-optimized settings
            self._model = await loop.run_in_executor(
                None,
                lambda: AutoModelForSeq2SeqLM.from_pretrained(
                    model_path,
                    cache_dir=str(self._models_dir / "flan-t5-small"),
                    torch_dtype=torch.float32,  # Use float32 for CPU
                    device_map=None,  # No device mapping for CPU
                    low_cpu_mem_usage=True  # Optimize for low memory
                )
            )
            
            # Move to CPU if not already there
            self._model = self._model.to('cpu')
            
            # Set to evaluation mode
            self._model.eval()
            
            self._is_loaded = True
            self.logger.info("✓ Flan-T5-small model loaded successfully")
            
        except ImportError as e:
            self.logger.error(f"Missing dependencies for Flan-T5: {e}")
            raise RuntimeError("Flan-T5 dependencies not installed. Please install: pip install transformers torch")
        except Exception as e:
            self.logger.error(f"Failed to load Flan-T5 model: {e}")
            raise
    
    async def rewrite_text(self, text: str, mode: RewriteMode) -> str:
        """
        Rewrite text using the specified mode
        
        Args:
            text: Input text to rewrite (max ~200 tokens)
            mode: Rewriting mode
            
        Returns:
            Rewritten text
        """
        # Ensure model is loaded
        await self._load_model()
        
        try:
            # Prepare the prompt
            if mode not in self._prompts:
                raise ValueError(f"Unsupported rewrite mode: {mode}")
            
            prompt = self._prompts[mode].format(text=text.strip())
            
            # Truncate input if too long (approximate token limit)
            if len(prompt) > 800:  # Conservative limit for ~200 tokens
                text_limit = 800 - len(self._prompts[mode]) + len("{text}")
                truncated_text = text[:text_limit] + "..."
                prompt = self._prompts[mode].format(text=truncated_text)
                self.logger.warning(f"Input text truncated to fit token limit")
            
            self.logger.debug(f"Rewriting with mode '{mode}': {prompt[:100]}...")
            
            # Run inference in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._generate_text,
                prompt
            )
            
            # Clean up the result
            result = result.strip()
            
            # Remove the original prompt if it appears in the result
            if result.startswith(prompt):
                result = result[len(prompt):].strip()
            
            self.logger.debug(f"Rewrite result: {result[:100]}...")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to rewrite text: {e}")
            raise
    
    def _generate_text(self, prompt: str) -> str:
        """Generate text using the T5 model (runs in thread pool)"""
        try:
            import torch
            
            # Tokenize input
            inputs = self._tokenizer.encode(
                prompt,
                return_tensors="pt",
                max_length=512,
                truncation=True
            )
            
            # Generate with CPU-optimized parameters
            with torch.no_grad():
                outputs = self._model.generate(
                    inputs,
                    max_length=200,
                    min_length=10,
                    num_beams=2,  # Reduced for speed
                    early_stopping=True,
                    do_sample=False,
                    temperature=0.7,
                    pad_token_id=self._tokenizer.eos_token_id
                )
            
            # Decode the result
            result = self._tokenizer.decode(
                outputs[0],
                skip_special_tokens=True
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Text generation failed: {e}")
            raise
    
    async def health_check(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if the T5 rewriter service is healthy
        
        Returns:
            Tuple of (is_healthy: bool, details: dict)
        """
        details = {
            "model_loaded": self._is_loaded,
            "models_dir_exists": self._models_dir.exists(),
            "local_model_exists": (self._models_dir / "flan-t5-small" / "local_model").exists()
        }
        
        try:
            if not self._is_loaded:
                # Try to load the model
                await self._load_model()
            
            # Test with a simple rewrite
            test_text = "This sentence have a grammar error."
            result = await self.rewrite_text(test_text, RewriteMode.FIX)
            
            details["test_input"] = test_text
            details["test_output"] = result
            details["test_passed"] = len(result) > 0 and result != test_text
            
            return details["test_passed"], details
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            details["error"] = str(e)
            return False, details
    
    async def get_supported_modes(self) -> Dict[str, str]:
        """Get supported rewriting modes with descriptions"""
        return {
            "fix": "Correct grammar and spelling errors",
            "concise": "Make text more concise and to the point",
            "formal": "Rewrite in a formal, professional tone",
            "friendly": "Rewrite in a friendly, conversational tone"
        }
    
    async def cleanup(self) -> None:
        """Clean up resources"""
        if self._model:
            try:
                # Clear model from memory
                del self._model
                del self._tokenizer
                
                # Force garbage collection
                import gc
                gc.collect()
                
                self.logger.info("T5 rewriter service cleaned up")
            except Exception as e:
                self.logger.error(f"Error during cleanup: {e}")
            finally:
                self._model = None
                self._tokenizer = None
                self._is_loaded = False
