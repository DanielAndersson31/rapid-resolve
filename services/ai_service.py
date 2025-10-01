import base64
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import logging

import openai
from openai import OpenAI
import whisper

from app.config import settings

logger = logging.getLogger(__name__)


class AIService:
    """
    AI service using pre-trained models for multimodal processing.
    Handles image analysis, audio transcription, and text understanding.
    """
    
    def __init__(self):
        """Initialize AI service with OpenAI client"""
        try:
            self.openai_client = OpenAI(api_key=settings.openai_api_key)
            self.whisper_model = None  # Lazy load
            
            logger.info("AI service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize AI service: {e}")
            raise
    
    def _load_whisper_model(self):
        """Lazy load Whisper model (only when needed)"""
        if self.whisper_model is None:
            logger.info(f"Loading Whisper model: {settings.whisper_model}")
            self.whisper_model = whisper.load_model(settings.whisper_model)
            logger.info("Whisper model loaded")
        return self.whisper_model
    
    # ==================== Image Analysis ====================
    
    def analyze_image(
        self,
        image_data: bytes,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze image using OpenAI Vision.
        
        Args:
            image_data: Binary image data
            context: Optional context about the image
        
        Returns:
            Dict with content_type, detected_text, visual_elements, technical_details, relevance_score
        """
        try:
            # Encode image to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Build prompt
            system_prompt = """You are an expert at analyzing technical support images. 
            Analyze the image and extract:
            1. Type of image (screenshot, photo, diagram, error_dialog)
            2. Any text visible (error messages, codes, UI elements)
            3. Visual elements (buttons, icons, error indicators)
            4. Technical details (error codes, system info, hardware issues)
            5. Relevance to technical support (0-1 score)
            
            Return as JSON with keys: content_type, detected_text (array), visual_elements (array), 
            technical_details (object), relevance_score (float)"""
            
            user_prompt = "Analyze this technical support image."
            if context:
                user_prompt += f"\n\nContext: {context}"
            
            # Call OpenAI Vision
            response = self.openai_client.chat.completions.create(
                model=settings.openai_vision_model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": user_prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            logger.info(f"Image analysis complete: {result.get('content_type', 'unknown')}")
            return result
            
        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            return {
                "content_type": "unknown",
                "detected_text": [],
                "visual_elements": [],
                "technical_details": {},
                "relevance_score": 0.0,
                "error": str(e)
            }
    
    # ==================== Audio Transcription ====================
    
    def transcribe_audio(
        self,
        audio_file_path: str,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Transcribe audio using Whisper.
        
        Args:
            audio_file_path: Path to audio file
            language: Language code (default: 'en')
        
        Returns:
            Dict with transcription, language, duration, confidence, key_phrases
        """
        try:
            # Load Whisper model
            model = self._load_whisper_model()
            
            # Transcribe
            result = model.transcribe(
                audio_file_path,
                language=language,
                fp16=False  # Use FP32 for CPU compatibility
            )
            
            transcription = result["text"].strip()
            
            # Extract key phrases (simple word frequency for now)
            key_phrases = self._extract_key_phrases(transcription)
            
            # Analyze sentiment
            sentiment = self._analyze_sentiment(transcription)
            
            logger.info(f"Audio transcription complete: {len(transcription)} characters")
            
            return {
                "transcription": transcription,
                "language": result.get("language", language),
                "duration_seconds": 0.0,  # Whisper doesn't return duration directly
                "word_count": len(transcription.split()),
                "confidence": 0.9,  # Whisper doesn't provide confidence scores
                "key_phrases": key_phrases,
                "sentiment": sentiment
            }
            
        except Exception as e:
            logger.error(f"Audio transcription failed: {e}")
            return {
                "transcription": "",
                "language": language,
                "duration_seconds": 0.0,
                "word_count": 0,
                "confidence": 0.0,
                "key_phrases": [],
                "sentiment": "unknown",
                "error": str(e)
            }
    
    # ==================== Text Analysis ====================
    
    def analyze_text(
        self,
        text: str,
        conversation_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze text for intent, entities, emotion, and urgency.
        
        Args:
            text: Text content to analyze
            conversation_context: Optional conversation history
        
        Returns:
            Dict with intent, entities, emotion, urgency_score
        """
        try:
            system_prompt = """You are an expert customer service AI analyzing support requests.
            Analyze the text and provide:
            1. Intent: What does the customer want? (request_help, report_issue, solution_feedback, escalation_request)
            2. Entities: Extract products, error codes, technical terms
            3. Emotion: Sentiment and urgency level
            4. Urgency score: 0-1 float indicating how urgent this is
            
            Return as JSON."""
            
            user_prompt = f"Analyze this customer message:\n\n{text}"
            
            if conversation_context:
                user_prompt += f"\n\nPrevious context: {conversation_context.get('context_summary', 'None')}"
            
            response = self.openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=500
            )
            
            result = json.loads(response.choices[0].message.content)
            
            logger.info(f"Text analysis complete: intent={result.get('intent', {}).get('type', 'unknown')}")
            return result
            
        except Exception as e:
            logger.error(f"Text analysis failed: {e}")
            return {
                "intent": {"type": "request_help", "confidence": 0.5},
                "entities": {},
                "emotion": {"sentiment": "neutral", "urgency_level": "medium"},
                "urgency_score": 0.5,
                "error": str(e)
            }
    
    def classify_intent(
        self,
        text: str,
        previous_interactions: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Classify customer intent from text.
        
        Args:
            text: Customer message
            previous_interactions: Previous interaction history
        
        Returns:
            Dict with type, confidence, category, subcategory
        """
        analysis = self.analyze_text(text)
        return analysis.get("intent", {"type": "request_help", "confidence": 0.5})
    
    def extract_entities(self, text: str) -> Dict[str, Any]:
        """
        Extract entities from text (products, error codes, etc).
        
        Args:
            text: Text to analyze
        
        Returns:
            Dict with product_mentions, error_codes, technical_terms
        """
        analysis = self.analyze_text(text)
        return analysis.get("entities", {})
    
    def calculate_urgency(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Calculate urgency score from text and context.
        
        Args:
            text: Customer message
            context: Optional conversation context
        
        Returns:
            Float between 0-1 indicating urgency
        """
        analysis = self.analyze_text(text, context)
        return analysis.get("urgency_score", 0.5)
    
    # ==================== Solution Generation ====================
    
    def generate_solution(
        self,
        ticket_context: Dict[str, Any],
        previous_attempts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate contextual solution based on ticket history.
        
        Args:
            ticket_context: Full ticket context
            previous_attempts: Previous solution attempts
        
        Returns:
            Dict with content, steps, confidence, difficulty, requires_escalation
        """
        try:
            # Build context for solution generation
            system_prompt = """You are an expert technical support agent specializing in electronics troubleshooting.
            Generate a step-by-step solution based on the customer's issue and previous attempts.
            
            Consider:
            1. What solutions have already been tried
            2. Customer's technical skill level
            3. Urgency of the issue
            4. Whether escalation to human support is needed
            
            Return JSON with: content (string), steps (array of strings), confidence (0-1), 
            estimated_difficulty (easy/medium/hard), requires_escalation (boolean), 
            escalation_reason (string if needed), prerequisites (array)"""
            
            # Format ticket context
            ticket_info = ticket_context.get("ticket_info", {})
            conversations = ticket_context.get("conversation_flow", [])
            
            user_prompt = f"""
            Issue: {ticket_info.get('title', 'Unknown issue')}
            Description: {ticket_info.get('description', 'No description')}
            Category: {ticket_info.get('category', 'general')}
            Product: {ticket_info.get('product_type', 'unknown')}
            
            Conversation history:
            {self._format_conversation_history(conversations)}
            
            Previous solution attempts:
            {self._format_previous_attempts(previous_attempts)}
            
            Generate the next best solution.
            """
            
            response = self.openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=1500
            )
            
            result = json.loads(response.choices[0].message.content)
            
            logger.info(f"Solution generated with confidence: {result.get('confidence', 0)}")
            return result
            
        except Exception as e:
            logger.error(f"Solution generation failed: {e}")
            return {
                "content": "I apologize, but I'm having difficulty generating a solution. Let me escalate this to a human agent.",
                "steps": ["Contact human support for assistance"],
                "confidence": 0.1,
                "estimated_difficulty": "unknown",
                "requires_escalation": True,
                "escalation_reason": "AI processing error",
                "prerequisites": [],
                "error": str(e)
            }
    
    def generate_context_summary(
        self,
        ticket_title: str,
        description: str,
        interactions: List[Any]
    ) -> str:
        """
        Generate a concise context summary of the ticket.
        
        Args:
            ticket_title: Ticket title
            description: Ticket description
            interactions: List of interactions
        
        Returns:
            Summary string
        """
        try:
            system_prompt = "You are summarizing a customer support ticket. Create a brief, informative summary."
            
            interaction_texts = [
                f"- {getattr(i, 'interaction_type', 'unknown')}: {getattr(i, 'processed_content', getattr(i, 'raw_content', ''))[:100]}..."
                for i in interactions[:5]  # Last 5 interactions
            ]
            
            user_prompt = f"""
            Title: {ticket_title}
            Description: {description}
            
            Recent interactions:
            {chr(10).join(interaction_texts)}
            
            Provide a 2-3 sentence summary.
            """
            
            response = self.openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=200
            )
            
            summary = response.choices[0].message.content.strip()
            logger.info("Context summary generated")
            return summary
            
        except Exception as e:
            logger.error(f"Context summary generation failed: {e}")
            return f"Customer support case: {ticket_title}"
    
    # ==================== Helper Methods ====================
    
    def _extract_key_phrases(self, text: str, max_phrases: int = 5) -> List[str]:
        """Extract key phrases from text (simple implementation)"""
        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'was', 'are', 'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
        
        words = text.lower().split()
        phrases = [w for w in words if w not in stop_words and len(w) > 3]
        
        # Return unique phrases
        return list(dict.fromkeys(phrases))[:max_phrases]
    
    def _analyze_sentiment(self, text: str) -> str:
        """Simple sentiment analysis"""
        negative_words = ['frustrated', 'angry', 'upset', 'disappointed', 'broken', 'not working', 'failed', 'error', 'problem', 'issue']
        positive_words = ['thanks', 'thank you', 'great', 'works', 'working', 'fixed', 'solved', 'perfect', 'excellent']
        
        text_lower = text.lower()
        
        negative_count = sum(1 for word in negative_words if word in text_lower)
        positive_count = sum(1 for word in positive_words if word in text_lower)
        
        if negative_count > positive_count:
            return "frustrated"
        elif positive_count > negative_count:
            return "satisfied"
        else:
            return "neutral"
    
    def _format_conversation_history(self, conversations: List[Dict]) -> str:
        """Format conversation history for prompts"""
        if not conversations:
            return "No previous conversation"
        
        formatted = []
        for conv in conversations[-5:]:  # Last 5 turns
            speaker = conv.get('speaker', 'unknown')
            message = conv.get('message', '')[:200]  # Truncate long messages
            formatted.append(f"{speaker}: {message}")
        
        return "\n".join(formatted)
    
    def _format_previous_attempts(self, attempts: List[Dict]) -> str:
        """Format previous solution attempts"""
        if not attempts:
            return "No previous attempts"
        
        formatted = []
        for idx, attempt in enumerate(attempts):
            result = attempt.get('result', 'unknown')
            content = attempt.get('content', '')[:100]
            formatted.append(f"{idx + 1}. {content}... (Result: {result})")
        
        return "\n".join(formatted)


# Singleton instance
_ai_service_instance: Optional[AIService] = None


def get_ai_service() -> AIService:
    """
    Get AI service singleton instance.
    Used for dependency injection in FastAPI.
    """
    global _ai_service_instance
    if _ai_service_instance is None:
        _ai_service_instance = AIService()
    return _ai_service_instance