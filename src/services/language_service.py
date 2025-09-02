"""Language detection service for English and Swedish support."""

import logging
from typing import Dict, Optional, Tuple

from langdetect import detect, detect_langs, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

from ..config.settings import get_settings

logger = logging.getLogger(__name__)

# Set seed for consistent results
DetectorFactory.seed = 0


class LanguageDetectionService:
    """Service for detecting text language with fallback handling."""
    
    def __init__(self) -> None:
        """Initialize the language detection service."""
        self.settings = get_settings()
        self.supported_languages = set(self.settings.application.supported_languages)
        self.default_language = self.settings.application.default_language
        self.min_confidence = 0.7  # Minimum confidence for language detection
        self.min_text_length = 10  # Minimum text length for reliable detection
    
    def detect_language(self, text: str) -> Tuple[str, float]:
        """
        Detect the language of the given text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple of (language_code, confidence_score)
        """
        if not text or len(text.strip()) < self.min_text_length:
            logger.debug(f"Text too short for reliable detection, using default: {self.default_language}")
            return self.default_language, 0.5
        
        try:
            # Get language probabilities
            language_probs = detect_langs(text)
            
            if not language_probs:
                logger.debug("No language detected, using default")
                return self.default_language, 0.5
            
            # Get the most probable language
            top_language = language_probs[0]
            detected_lang = top_language.lang
            confidence = top_language.prob
            
            # Map language codes to our supported languages
            language_mapping = {
                "en": "en",
                "sv": "sv", 
                "no": "sv",  # Norwegian -> Swedish (similar)
                "da": "sv",  # Danish -> Swedish (similar)
            }
            
            mapped_language = language_mapping.get(detected_lang, detected_lang)
            
            # Check if detected language is supported
            if mapped_language in self.supported_languages:
                if confidence >= self.min_confidence:
                    logger.debug(f"Detected language: {mapped_language} (confidence: {confidence:.3f})")
                    return mapped_language, confidence
                else:
                    logger.debug(f"Low confidence detection: {mapped_language} ({confidence:.3f}), using default")
                    return self.default_language, confidence
            else:
                logger.debug(f"Unsupported language: {detected_lang}, using default: {self.default_language}")
                return self.default_language, confidence
        
        except LangDetectException as e:
            logger.debug(f"Language detection failed: {e}, using default: {self.default_language}")
            return self.default_language, 0.3
        except Exception as e:
            logger.warning(f"Unexpected error in language detection: {e}")
            return self.default_language, 0.3
    
    def detect_language_simple(self, text: str) -> str:
        """
        Simple language detection returning only the language code.
        
        Args:
            text: Text to analyze
            
        Returns:
            Language code
        """
        language, _ = self.detect_language(text)
        return language
    
    def is_supported_language(self, language_code: str) -> bool:
        """
        Check if a language code is supported.
        
        Args:
            language_code: Language code to check
            
        Returns:
            True if supported, False otherwise
        """
        return language_code in self.supported_languages
    
    def get_language_info(self, text: str) -> Dict[str, any]:
        """
        Get detailed language detection information.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with detection details
        """
        if not text:
            return {
                "detected_language": self.default_language,
                "confidence": 0.0,
                "is_supported": True,
                "method": "default",
                "text_length": 0,
                "all_probabilities": [],
            }
        
        text_length = len(text.strip())
        
        if text_length < self.min_text_length:
            return {
                "detected_language": self.default_language,
                "confidence": 0.5,
                "is_supported": True,
                "method": "fallback_short_text",
                "text_length": text_length,
                "all_probabilities": [],
            }
        
        try:
            # Get all language probabilities
            language_probs = detect_langs(text)
            all_probs = [{"language": lp.lang, "probability": lp.prob} for lp in language_probs]
            
            # Get primary detection
            detected_language, confidence = self.detect_language(text)
            
            return {
                "detected_language": detected_language,
                "confidence": confidence,
                "is_supported": self.is_supported_language(detected_language),
                "method": "langdetect",
                "text_length": text_length,
                "all_probabilities": all_probs,
            }
            
        except Exception as e:
            logger.warning(f"Error getting language info: {e}")
            return {
                "detected_language": self.default_language,
                "confidence": 0.3,
                "is_supported": True,
                "method": "fallback_error",
                "text_length": text_length,
                "all_probabilities": [],
                "error": str(e),
            }
    
    def validate_language_consistency(self, texts: list[str]) -> Dict[str, any]:
        """
        Validate language consistency across multiple texts.
        
        Args:
            texts: List of texts to check
            
        Returns:
            Consistency analysis
        """
        if not texts:
            return {
                "is_consistent": True,
                "primary_language": self.default_language,
                "languages_detected": [],
                "confidence": 1.0,
            }
        
        language_counts = {}
        total_confidence = 0.0
        
        for text in texts:
            if text and len(text.strip()) >= self.min_text_length:
                lang, conf = self.detect_language(text)
                language_counts[lang] = language_counts.get(lang, 0) + 1
                total_confidence += conf
        
        if not language_counts:
            return {
                "is_consistent": True,
                "primary_language": self.default_language,
                "languages_detected": [],
                "confidence": 0.5,
            }
        
        # Find most common language
        primary_language = max(language_counts, key=language_counts.get)
        unique_languages = list(language_counts.keys())
        
        # Calculate consistency
        is_consistent = len(unique_languages) == 1
        avg_confidence = total_confidence / len(texts) if texts else 0.0
        
        return {
            "is_consistent": is_consistent,
            "primary_language": primary_language,
            "languages_detected": unique_languages,
            "language_counts": language_counts,
            "confidence": avg_confidence,
        }
    
    def get_supported_languages(self) -> Dict[str, str]:
        """
        Get supported languages with their names.
        
        Returns:
            Dictionary of language codes and names
        """
        language_names = {
            "en": "English",
            "sv": "Svenska (Swedish)",
        }
        
        return {
            lang: language_names.get(lang, lang.upper())
            for lang in self.supported_languages
        }
    
    async def health_check(self) -> Dict[str, str]:
        """
        Perform health check on language detection service.
        
        Returns:
            Health status
        """
        try:
            # Test detection with sample texts
            test_texts = {
                "en": "Hello, this is a test message in English.",
                "sv": "Hej, detta är ett testmeddelande på svenska.",
            }
            
            results = {}
            overall_status = "healthy"
            
            for lang, text in test_texts.items():
                try:
                    detected, confidence = self.detect_language(text)
                    if detected == lang and confidence > 0.5:
                        results[f"{lang}_detection"] = "healthy"
                    else:
                        results[f"{lang}_detection"] = f"degraded (detected: {detected}, conf: {confidence:.2f})"
                        overall_status = "degraded"
                except Exception as e:
                    results[f"{lang}_detection"] = f"error: {str(e)}"
                    overall_status = "degraded"
            
            results["overall"] = overall_status
            results["supported_languages"] = ",".join(self.supported_languages)
            results["default_language"] = self.default_language
            
            return results
            
        except Exception as e:
            logger.error(f"Language detection health check failed: {e}")
            return {
                "overall": "unhealthy",
                "error": str(e)
            }


# Global service instance
_language_service: Optional[LanguageDetectionService] = None


def get_language_service() -> LanguageDetectionService:
    """Get the global language detection service instance."""
    global _language_service
    if _language_service is None:
        _language_service = LanguageDetectionService()
    return _language_service