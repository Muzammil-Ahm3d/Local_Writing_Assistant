"""
Tone Analysis Service for Local Writing Assistant

Provides heuristic-based tone analysis including sentiment and formality detection.
Uses linguistic patterns, punctuation, and word choices for analysis.
Completely offline with no external dependencies.
"""

import re
import logging
from typing import Dict, Any, Tuple, List, Optional
from enum import Enum
from dataclasses import dataclass


class Sentiment(str, Enum):
    """Sentiment categories"""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class Formality(str, Enum):
    """Formality categories"""
    FORMAL = "formal"
    NEUTRAL = "neutral"
    CASUAL = "casual"


@dataclass
class ToneAnalysis:
    """Represents tone analysis results"""
    sentiment: Sentiment
    formality: Formality
    scores: Dict[str, float]
    confidence: float
    features: Dict[str, Any]


class ToneAnalysisService:
    """Service for analyzing text tone using heuristic methods"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Load word lists and patterns
        self._load_lexicons()
        self._compile_patterns()
    
    def _load_lexicons(self):
        """Load word lists for sentiment and formality analysis"""
        # Positive sentiment words
        self.positive_words = {
            'excellent', 'great', 'amazing', 'wonderful', 'fantastic', 'awesome',
            'love', 'like', 'enjoy', 'appreciate', 'pleased', 'happy', 'glad',
            'good', 'nice', 'perfect', 'brilliant', 'outstanding', 'superb',
            'delighted', 'thrilled', 'excited', 'satisfied', 'impressed',
            'thank', 'thanks', 'grateful', 'blessing', 'fortunate', 'lucky'
        }
        
        # Negative sentiment words
        self.negative_words = {
            'terrible', 'awful', 'horrible', 'bad', 'worst', 'hate', 'dislike',
            'disappointed', 'frustrated', 'angry', 'annoyed', 'upset', 'sad',
            'wrong', 'problem', 'issue', 'error', 'mistake', 'fail', 'failure',
            'difficult', 'hard', 'challenging', 'struggle', 'trouble', 'worry',
            'concerned', 'unfortunately', 'regret', 'sorry', 'apologize'
        }
        
        # Formal words and phrases
        self.formal_words = {
            'furthermore', 'moreover', 'consequently', 'therefore', 'nevertheless',
            'notwithstanding', 'accordingly', 'subsequently', 'henceforth',
            'pursuant', 'regarding', 'concerning', 'pertaining', 'whereby',
            'heretofore', 'aforementioned', 'undersigned', 'herewith',
            'establish', 'facilitate', 'implement', 'utilize', 'demonstrate',
            'indicate', 'constitute', 'represent', 'acknowledge', 'endeavor'
        }
        
        # Casual words and phrases
        self.casual_words = {
            'yeah', 'yep', 'nope', 'gonna', 'wanna', 'gotta', 'kinda', 'sorta',
            'stuff', 'thing', 'things', 'guys', 'dude', 'awesome', 'cool',
            'super', 'really', 'pretty', 'quite', 'totally', 'definitely',
            'basically', 'literally', 'actually', 'obviously', 'seriously',
            'honestly', 'frankly', 'btw', 'fyi', 'imho', 'tbh'
        }
        
        # Contractions (indicate casual tone)
        self.contractions = {
            "won't", "can't", "don't", "didn't", "hasn't", "haven't", "isn't",
            "aren't", "wasn't", "weren't", "shouldn't", "wouldn't", "couldn't",
            "I'm", "you're", "he's", "she's", "it's", "we're", "they're",
            "I've", "you've", "we've", "they've", "I'd", "you'd", "he'd",
            "she'd", "we'd", "they'd", "I'll", "you'll", "he'll", "she'll",
            "we'll", "they'll", "that's", "what's", "who's", "where's"
        }
    
    def _compile_patterns(self):
        """Compile regular expressions for pattern matching"""
        # Exclamation patterns (enthusiasm/emotion)
        self.exclamation_pattern = re.compile(r'!+')
        
        # Question patterns
        self.question_pattern = re.compile(r'\?+')
        
        # All caps words (emphasis/shouting)
        self.caps_pattern = re.compile(r'\b[A-Z]{2,}\b')
        
        # Ellipsis patterns (uncertainty/trailing off)
        self.ellipsis_pattern = re.compile(r'\.{3,}')
        
        # Emoticons and emojis (simple detection)
        self.emoticon_pattern = re.compile(r'[:;=]-?[)D(P\\/]|[)D(P\\/]-?[:;=]')
        
        # Word patterns
        self.word_pattern = re.compile(r'\b\w+\b', re.IGNORECASE)
    
    def analyze_tone(self, text: str) -> ToneAnalysis:
        """
        Analyze the tone of the given text
        
        Args:
            text: Input text to analyze
            
        Returns:
            ToneAnalysis object with sentiment, formality, and details
        """
        if not text.strip():
            return ToneAnalysis(
                sentiment=Sentiment.NEUTRAL,
                formality=Formality.NEUTRAL,
                scores={'sentiment': 0.0, 'formality': 0.0},
                confidence=0.0,
                features={}
            )
        
        # Extract features
        features = self._extract_features(text)
        
        # Analyze sentiment
        sentiment, sentiment_score = self._analyze_sentiment(text, features)
        
        # Analyze formality
        formality, formality_score = self._analyze_formality(text, features)
        
        # Calculate overall confidence
        confidence = self._calculate_confidence(features, sentiment_score, formality_score)
        
        return ToneAnalysis(
            sentiment=sentiment,
            formality=formality,
            scores={
                'sentiment': sentiment_score,
                'formality': formality_score
            },
            confidence=confidence,
            features=features
        )
    
    def _extract_features(self, text: str) -> Dict[str, Any]:
        """Extract linguistic features from text"""
        text_lower = text.lower()
        words = self.word_pattern.findall(text_lower)
        
        features = {
            # Basic stats
            'word_count': len(words),
            'char_count': len(text),
            'sentence_count': len([s for s in re.split(r'[.!?]+', text) if s.strip()]),
            'avg_word_length': sum(len(w) for w in words) / max(len(words), 1),
            
            # Punctuation features
            'exclamation_count': len(self.exclamation_pattern.findall(text)),
            'question_count': len(self.question_pattern.findall(text)),
            'caps_words': len(self.caps_pattern.findall(text)),
            'ellipsis_count': len(self.ellipsis_pattern.findall(text)),
            'emoticon_count': len(self.emoticon_pattern.findall(text)),
            
            # Lexical features
            'positive_word_count': sum(1 for w in words if w in self.positive_words),
            'negative_word_count': sum(1 for w in words if w in self.negative_words),
            'formal_word_count': sum(1 for w in words if w in self.formal_words),
            'casual_word_count': sum(1 for w in words if w in self.casual_words),
            'contraction_count': sum(1 for w in text.split() if w.lower() in self.contractions),
        }
        
        # Ratios
        word_count = max(features['word_count'], 1)
        features.update({
            'positive_ratio': features['positive_word_count'] / word_count,
            'negative_ratio': features['negative_word_count'] / word_count,
            'formal_ratio': features['formal_word_count'] / word_count,
            'casual_ratio': features['casual_word_count'] / word_count,
            'contraction_ratio': features['contraction_count'] / word_count,
            'caps_ratio': features['caps_words'] / word_count,
            'exclamation_ratio': features['exclamation_count'] / max(features['sentence_count'], 1)
        })
        
        return features
    
    def _analyze_sentiment(self, text: str, features: Dict[str, Any]) -> Tuple[Sentiment, float]:
        """Analyze sentiment using heuristic rules"""
        # Base sentiment score from word counts
        positive_score = features['positive_ratio'] * 2.0
        negative_score = features['negative_ratio'] * 2.0
        
        # Adjust for punctuation
        if features['exclamation_count'] > 0:
            # Exclamations can amplify existing sentiment
            if positive_score > negative_score:
                positive_score += features['exclamation_ratio'] * 0.5
            elif negative_score > positive_score:
                negative_score += features['exclamation_ratio'] * 0.5
        
        # Adjust for emoticons (simple heuristic)
        if features['emoticon_count'] > 0:
            positive_score += 0.2  # Assume emoticons are generally positive
        
        # Adjust for caps (can indicate strong emotion)
        if features['caps_ratio'] > 0.1:  # More than 10% caps words
            if positive_score > negative_score:
                positive_score += 0.3
            else:
                negative_score += 0.3
        
        # Calculate final sentiment score (-1 to 1)
        net_score = positive_score - negative_score
        
        # Determine sentiment category
        if net_score > 0.2:
            sentiment = Sentiment.POSITIVE
        elif net_score < -0.2:
            sentiment = Sentiment.NEGATIVE
        else:
            sentiment = Sentiment.NEUTRAL
        
        return sentiment, net_score
    
    def _analyze_formality(self, text: str, features: Dict[str, Any]) -> Tuple[Formality, float]:
        """Analyze formality using heuristic rules"""
        # Base formality score
        formal_score = features['formal_ratio'] * 3.0
        casual_score = features['casual_ratio'] * 2.0
        
        # Contractions strongly indicate casual tone
        casual_score += features['contraction_ratio'] * 2.0
        
        # Punctuation adjustments
        if features['exclamation_ratio'] > 0.5:  # Many exclamations
            casual_score += 0.5
        
        if features['ellipsis_count'] > 0:  # Ellipsis usage
            casual_score += 0.3
        
        # Word length adjustment (longer words suggest formality)
        if features['avg_word_length'] > 5.5:
            formal_score += 0.5
        elif features['avg_word_length'] < 4.0:
            casual_score += 0.3
        
        # Sentence length adjustment
        if features['word_count'] > 0 and features['sentence_count'] > 0:
            avg_sentence_length = features['word_count'] / features['sentence_count']
            if avg_sentence_length > 15:  # Long sentences suggest formality
                formal_score += 0.4
            elif avg_sentence_length < 8:  # Short sentences suggest casualness
                casual_score += 0.3
        
        # Calculate final formality score (-1 to 1, negative=casual, positive=formal)
        net_score = formal_score - casual_score
        
        # Determine formality category
        if net_score > 0.5:
            formality = Formality.FORMAL
        elif net_score < -0.5:
            formality = Formality.CASUAL
        else:
            formality = Formality.NEUTRAL
        
        return formality, net_score
    
    def _calculate_confidence(self, features: Dict[str, Any], sentiment_score: float, formality_score: float) -> float:
        """Calculate confidence in the analysis"""
        # Base confidence on text length (longer texts are more reliable)
        word_count = features['word_count']
        length_confidence = min(word_count / 50.0, 1.0)  # Max confidence at 50+ words
        
        # Factor in feature strength
        sentiment_strength = abs(sentiment_score)
        formality_strength = abs(formality_score)
        
        feature_confidence = (sentiment_strength + formality_strength) / 2.0
        
        # Combine confidences
        overall_confidence = (length_confidence * 0.6) + (feature_confidence * 0.4)
        
        return min(max(overall_confidence, 0.1), 1.0)  # Clamp to [0.1, 1.0]
    
    async def health_check(self) -> Tuple[bool, Dict[str, Any]]:
        """Check if the tone analysis service is healthy"""
        details = {
            "lexicons_loaded": True,
            "patterns_compiled": True,
            "positive_words": len(self.positive_words),
            "negative_words": len(self.negative_words),
            "formal_words": len(self.formal_words),
            "casual_words": len(self.casual_words)
        }
        
        try:
            # Test with sample text
            test_text = "I'm really excited about this amazing opportunity!"
            analysis = self.analyze_tone(test_text)
            
            details.update({
                "test_input": test_text,
                "test_sentiment": analysis.sentiment.value,
                "test_formality": analysis.formality.value,
                "test_confidence": analysis.confidence,
                "test_passed": analysis.sentiment == Sentiment.POSITIVE and analysis.confidence > 0.3
            })
            
            return details["test_passed"], details
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            details["error"] = str(e)
            return False, details
