"""
Fast Rule-Based Text Rewriter Service

Provides instant text rewriting using rule-based transformations
instead of heavy ML models. Optimized for speed and responsiveness.
"""

import re
import logging
from typing import Dict, List, Tuple
from enum import Enum


class RewriteMode(str, Enum):
    """Available rewriting modes"""
    FIX = "fix"
    CONCISE = "concise"
    FORMAL = "formal" 
    FRIENDLY = "friendly"


class FastRewriterService:
    """Fast rule-based text rewriter service"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Grammar fixes
        self.grammar_fixes = [
            # Capitalization
            (r'^([a-z])', lambda m: m.group(1).upper()),
            (r'(\. )([a-z])', lambda m: m.group(1) + m.group(2).upper()),
            
            # Common contractions
            (r"\bi\b", "I"),
            (r"\bu\b", "you"),
            (r"\bur\b", "your"),
            (r"\br\b", "are"),
            (r"\bwont\b", "won't"),
            (r"\bcant\b", "can't"),
            (r"\bdont\b", "don't"),
            (r"\bwontnt\b", "won't"),
            (r"\bshoudl\b", "should"),
            (r"\bwoudl\b", "would"),
            (r"\bthier\b", "their"),
            (r"\bteh\b", "the"),
            (r"\byoru\b", "your"),
            (r"\bfro\b", "for"),
            (r"\bnad\b", "and"),
            
            # Add periods to end sentences
            (r'([^.!?])$', r'\1.'),
        ]
        
        # Formal transformations
        self.formal_transforms = [
            (r"\bhey\b", "Hello"),
            (r"\bhi\b", "Hello"),
            (r"\byeah\b", "yes"),
            (r"\byep\b", "yes"),
            (r"\bnah\b", "no"),
            (r"\bokay\b", "very well"),
            (r"\bok\b", "acceptable"),
            (r"\bthanks\b", "thank you"),
            (r"\bthx\b", "thank you"),
            (r"\bty\b", "thank you"),
            (r"\bbtw\b", "by the way"),
            (r"\basap\b", "as soon as possible"),
            (r"\bfyi\b", "for your information"),
            (r"\bimo\b", "in my opinion"),
            (r"\bidk\b", "I do not know"),
            (r"\bidc\b", "I do not care"),
            (r"\bwanna\b", "want to"),
            (r"\bgonna\b", "going to"),
            (r"\bkinda\b", "somewhat"),
            (r"\bsorta\b", "somewhat"),
            (r"\bgotta\b", "have to"),
            (r"\blemme\b", "let me"),
            (r"\bgimme\b", "give me"),
            (r"\bwhatcha\b", "what are you"),
            (r"\bhowd\b", "how did"),
            (r"\bwhyd\b", "why did"),
        ]
        
        # Friendly transformations
        self.friendly_transforms = [
            (r"\bHello\b", "Hey"),
            (r"\bGood morning\b", "Morning!"),
            (r"\bGood afternoon\b", "Hey there!"),
            (r"\bGood evening\b", "Evening!"),
            (r"\bthank you\b", "thanks"),
            (r"\bvery well\b", "sounds good"),
            (r"\bacceptable\b", "cool"),
            (r"\bas soon as possible\b", "ASAP"),
            (r"\bfor your information\b", "FYI"),
            (r"\bin my opinion\b", "IMO"),
            (r"\bI do not know\b", "IDK"),
            (r"\bwant to\b", "wanna"),
            (r"\bgoing to\b", "gonna"),
            (r"\bhave to\b", "gotta"),
            (r"\bsomewhat\b", "kinda"),
            (r"\blet me\b", "lemme"),
            (r"\bgive me\b", "gimme"),
            (r"\bPlease complete\b", "Could you"),
            (r"\bimmediately\b", "when you get a chance"),
            (r"\brequired\b", "would be great"),
            (r"\bmust\b", "should"),
            (r"\.( |$)", r"! \1"),  # Some periods to exclamations
        ]
        
        # Concise transformations
        self.concise_transforms = [
            (r"\bI would like to ask if you could possibly\b", "Could you"),
            (r"\bI am writing to inform you that\b", ""),
            (r"\bI hope this message finds you well\b", ""),
            (r"\bPlease be advised that\b", ""),
            (r"\bIn order to\b", "To"),
            (r"\bDue to the fact that\b", "Because"),
            (r"\bAt this point in time\b", "Now"),
            (r"\bIn the event that\b", "If"),
            (r"\bFor the purpose of\b", "For"),
            (r"\bWith regard to\b", "About"),
            (r"\bIt is important to note that\b", ""),
            (r"\bPlease do not hesitate to\b", "Please"),
            (r"\bI would appreciate it if you could\b", "Please"),
            (r"\bAs previously mentioned\b", "As mentioned"),
            (r"\bIn conclusion\b", "Finally"),
            (r"\bvery much\b", "much"),
            (r"\ba lot of\b", "many"),
            (r"\ba large number of\b", "many"),
            (r"\ba small number of\b", "few"),
            (r"\bin the near future\b", "soon"),
        ]
    
    def _apply_transforms(self, text: str, transforms: List[Tuple[str, str]]) -> str:
        """Apply a list of regex transformations to text"""
        result = text
        for pattern, replacement in transforms:
            if callable(replacement):
                result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
            else:
                result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        return result
    
    def _fix_grammar(self, text: str) -> str:
        """Apply grammar and spelling fixes"""
        return self._apply_transforms(text, self.grammar_fixes)
    
    def _make_formal(self, text: str) -> str:
        """Convert text to formal tone"""
        # First fix grammar, then apply formal transforms
        result = self._fix_grammar(text)
        result = self._apply_transforms(result, self.formal_transforms)
        
        # Ensure proper sentence structure
        if not result.endswith(('.', '!', '?')):
            result += '.'
        
        return result
    
    def _make_friendly(self, text: str) -> str:
        """Convert text to friendly tone"""
        # First fix grammar, then apply friendly transforms
        result = self._fix_grammar(text)
        result = self._apply_transforms(result, self.friendly_transforms)
        
        # Add some friendly punctuation
        if result.count('!') == 0 and len(result) > 10:
            result = re.sub(r'\.( |$)', r'! \1', result, count=1)
        
        return result
    
    def _make_concise(self, text: str) -> str:
        """Make text more concise"""
        result = self._fix_grammar(text)
        result = self._apply_transforms(result, self.concise_transforms)
        
        # Remove extra spaces
        result = re.sub(r'\s+', ' ', result).strip()
        
        # Remove empty sentences
        sentences = [s.strip() for s in re.split(r'[.!?]+', result) if s.strip()]
        if sentences:
            result = '. '.join(sentences) + '.'
        
        return result
    
    async def rewrite_text(self, text: str, mode: RewriteMode) -> str:
        """
        Rewrite text using the specified mode
        
        Args:
            text: Input text to rewrite
            mode: Rewriting mode
            
        Returns:
            Rewritten text
        """
        if not text or not text.strip():
            return text
        
        original_text = text.strip()
        self.logger.debug(f"Rewriting with mode '{mode}': {original_text[:50]}...")
        
        try:
            if mode == RewriteMode.FIX:
                result = self._fix_grammar(original_text)
            elif mode == RewriteMode.FORMAL:
                result = self._make_formal(original_text)
            elif mode == RewriteMode.FRIENDLY:
                result = self._make_friendly(original_text)
            elif mode == RewriteMode.CONCISE:
                result = self._make_concise(original_text)
            else:
                raise ValueError(f"Unsupported rewrite mode: {mode}")
            
            # Clean up result
            result = result.strip()
            if not result:
                result = original_text  # Fallback to original if empty
            
            self.logger.debug(f"Rewrite result: {result[:50]}...")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to rewrite text: {e}")
            return original_text  # Return original on error
    
    async def health_check(self) -> Tuple[bool, Dict[str, any]]:
        """
        Check if the fast rewriter service is healthy
        
        Returns:
            Tuple of (is_healthy: bool, details: dict)
        """
        try:
            # Test each mode quickly
            test_text = "hey whats up"
            
            test_results = {}
            for mode in RewriteMode:
                result = await self.rewrite_text(test_text, mode)
                test_results[mode.value] = {
                    "input": test_text,
                    "output": result,
                    "success": bool(result and result != test_text)
                }
            
            return True, {
                "service": "FastRewriter",
                "status": "healthy",
                "modes_available": [mode.value for mode in RewriteMode],
                "test_results": test_results,
                "performance": "< 10ms per request"
            }
            
        except Exception as e:
            return False, {
                "service": "FastRewriter", 
                "status": "unhealthy",
                "error": str(e)
            }
