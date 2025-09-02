"""Product validation for electronics categories."""

import logging
import re
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class ProductCategory(str, Enum):
    """Electronics product categories."""
    LAPTOPS = "laptops"
    PHONES = "phones"
    ACCESSORIES = "accessories"


class ProductValidator:
    """Validator for electronics product categories and specifications."""
    
    def __init__(self) -> None:
        """Initialize the product validator."""
        self._category_keywords = self._build_category_keywords()
        self._brand_patterns = self._build_brand_patterns()
        self._model_patterns = self._build_model_patterns()
    
    def _build_category_keywords(self) -> Dict[ProductCategory, Set[str]]:
        """Build keyword sets for each product category."""
        return {
            ProductCategory.LAPTOPS: {
                # Device types
                "laptop", "notebook", "ultrabook", "chromebook", "macbook",
                "thinkpad", "surface", "gaming laptop", "workstation",
                
                # Components
                "screen", "display", "keyboard", "trackpad", "battery",
                "charger", "ram", "ssd", "hard drive", "processor", "cpu",
                "graphics", "gpu", "cooling", "fan",
                
                # Issues
                "won't boot", "black screen", "overheating", "slow performance",
                "battery life", "charging", "power adapter", "screen flicker",
            },
            
            ProductCategory.PHONES: {
                # Device types
                "phone", "smartphone", "mobile", "iphone", "android",
                "samsung", "pixel", "galaxy", "oneplus",
                
                # Components
                "screen", "display", "camera", "battery", "speaker",
                "microphone", "charging port", "headphone jack",
                "sim card", "memory", "storage",
                
                # Issues
                "cracked screen", "won't charge", "no sound", "camera not working",
                "slow", "freezing", "restart", "overheating", "water damage",
            },
            
            ProductCategory.ACCESSORIES: {
                # Types
                "headphones", "earbuds", "airpods", "speaker", "charger",
                "cable", "adapter", "case", "cover", "screen protector",
                "mouse", "keyboard", "webcam", "microphone", "dock",
                "hub", "stand", "mount", "bag", "sleeve",
                
                # Issues
                "not connecting", "bluetooth", "pairing", "audio quality",
                "charging issue", "compatibility", "fit", "loose",
            },
        }
    
    def _build_brand_patterns(self) -> Dict[str, List[str]]:
        """Build brand recognition patterns."""
        return {
            "laptops": [
                "apple", "macbook", "dell", "xps", "inspiron", "alienware",
                "hp", "pavilion", "envy", "spectre", "omen",
                "lenovo", "thinkpad", "ideapad", "yoga",
                "asus", "zenbook", "vivobook", "rog",
                "acer", "aspire", "predator", "swift",
                "microsoft", "surface",
                "msi", "gaming", "razer", "blade",
            ],
            "phones": [
                "apple", "iphone", "samsung", "galaxy", "note",
                "google", "pixel", "oneplus", "huawei", "xiaomi",
                "nokia", "motorola", "lg", "sony", "xperia",
            ],
            "accessories": [
                "apple", "airpods", "magic", "logitech", "bose",
                "sony", "samsung", "anker", "belkin", "razer",
                "corsair", "steelseries", "hyperx", "jabra",
            ],
        }
    
    def _build_model_patterns(self) -> Dict[str, List[str]]:
        """Build model number recognition patterns."""
        return {
            # Common model number patterns
            "laptop_models": [
                r"xps\s*\d+", r"thinkpad\s*[a-z]\d+", r"macbook\s*(pro|air)",
                r"surface\s*(pro|laptop|book)", r"pavilion\s*\d+",
                r"inspiron\s*\d+", r"ideapad\s*\d+", r"zenbook\s*\d+",
            ],
            "phone_models": [
                r"iphone\s*\d+", r"galaxy\s*s\d+", r"pixel\s*\d+",
                r"oneplus\s*\d+", r"note\s*\d+", r"xperia\s*\d+",
            ],
        }
    
    def detect_category(self, text: str) -> Tuple[Optional[ProductCategory], float]:
        """
        Detect product category from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple of (detected_category, confidence_score)
        """
        if not text:
            return None, 0.0
        
        text_lower = text.lower()
        category_scores = {}
        
        # Score each category based on keyword matches
        for category, keywords in self._category_keywords.items():
            score = 0.0
            matched_keywords = set()
            
            for keyword in keywords:
                if keyword in text_lower:
                    # Weight based on keyword specificity
                    weight = 2.0 if len(keyword.split()) > 1 else 1.0
                    score += weight
                    matched_keywords.add(keyword)
            
            # Normalize score by text length
            normalized_score = score / (len(text_lower.split()) + 1)
            category_scores[category] = {
                "score": normalized_score,
                "matched_keywords": matched_keywords,
            }
        
        if not category_scores:
            return None, 0.0
        
        # Find category with highest score
        best_category = max(
            category_scores.keys(),
            key=lambda cat: category_scores[cat]["score"]
        )
        
        best_score = category_scores[best_category]["score"]
        
        # Set minimum confidence threshold
        if best_score < 0.1:
            return None, best_score
        
        return best_category, min(best_score, 1.0)
    
    def extract_brand(self, text: str, category: Optional[ProductCategory] = None) -> Optional[str]:
        """
        Extract brand information from text.
        
        Args:
            text: Text to analyze
            category: Product category to focus search
            
        Returns:
            Detected brand or None
        """
        if not text:
            return None
        
        text_lower = text.lower()
        
        # If category is known, focus on that category's brands
        if category:
            category_key = category.value
            brand_list = self._brand_patterns.get(category_key, [])
        else:
            # Search all brands
            brand_list = []
            for brands in self._brand_patterns.values():
                brand_list.extend(brands)
        
        # Find brand matches
        for brand in brand_list:
            if brand.lower() in text_lower:
                return brand.title()
        
        return None
    
    def extract_model(self, text: str, category: Optional[ProductCategory] = None) -> Optional[str]:
        """
        Extract model information from text.
        
        Args:
            text: Text to analyze
            category: Product category to focus search
            
        Returns:
            Detected model or None
        """
        if not text:
            return None
        
        # Determine which patterns to use
        if category == ProductCategory.LAPTOPS:
            patterns = self._model_patterns.get("laptop_models", [])
        elif category == ProductCategory.PHONES:
            patterns = self._model_patterns.get("phone_models", [])
        else:
            # Use all patterns
            patterns = []
            for pattern_list in self._model_patterns.values():
                patterns.extend(pattern_list)
        
        # Search for model patterns
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group().strip()
        
        return None
    
    def validate_product_info(self, text: str) -> Dict[str, any]:
        """
        Comprehensive product information validation and extraction.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with validation results
        """
        result = {
            "is_valid": False,
            "category": None,
            "confidence": 0.0,
            "brand": None,
            "model": None,
            "matched_keywords": [],
            "validation_errors": [],
        }
        
        if not text or len(text.strip()) < 5:
            result["validation_errors"].append("Text too short for product analysis")
            return result
        
        # Detect category
        category, confidence = self.detect_category(text)
        
        if category:
            result["category"] = category.value
            result["confidence"] = confidence
            result["is_valid"] = confidence > 0.2
            
            # Extract additional information
            result["brand"] = self.extract_brand(text, category)
            result["model"] = self.extract_model(text, category)
            
            # Get matched keywords
            keywords = self._category_keywords[category]
            text_lower = text.lower()
            matched = [kw for kw in keywords if kw in text_lower]
            result["matched_keywords"] = matched
            
        else:
            result["validation_errors"].append("No product category detected")
        
        return result
    
    def is_valid_category(self, category: str) -> bool:
        """
        Check if a category string is valid.
        
        Args:
            category: Category string
            
        Returns:
            True if valid, False otherwise
        """
        try:
            ProductCategory(category)
            return True
        except ValueError:
            return False
    
    def get_supported_categories(self) -> List[str]:
        """
        Get list of supported product categories.
        
        Returns:
            List of category strings
        """
        return [category.value for category in ProductCategory]
    
    def get_category_keywords(self, category: str) -> List[str]:
        """
        Get keywords for a specific category.
        
        Args:
            category: Category string
            
        Returns:
            List of keywords
        """
        try:
            cat_enum = ProductCategory(category)
            return list(self._category_keywords[cat_enum])
        except ValueError:
            return []
    
    def suggest_category(self, text: str, threshold: float = 0.1) -> List[Tuple[str, float]]:
        """
        Suggest possible categories with confidence scores.
        
        Args:
            text: Text to analyze
            threshold: Minimum confidence threshold
            
        Returns:
            List of (category, confidence) tuples
        """
        if not text:
            return []
        
        suggestions = []
        
        for category in ProductCategory:
            _, confidence = self.detect_category(text)
            if confidence >= threshold:
                suggestions.append((category.value, confidence))
        
        # Sort by confidence
        suggestions.sort(key=lambda x: x[1], reverse=True)
        
        return suggestions


# Global validator instance
_product_validator: Optional[ProductValidator] = None


def get_product_validator() -> ProductValidator:
    """Get the global product validator instance."""
    global _product_validator
    if _product_validator is None:
        _product_validator = ProductValidator()
    return _product_validator