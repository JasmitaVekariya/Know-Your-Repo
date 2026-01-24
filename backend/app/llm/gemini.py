"""Google Gemini LLM client integration."""

import google.generativeai as genai
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class GeminiClient:
    """Client for interacting with Google Gemini API."""
    
    def __init__(self, api_key: str):
        """
        Initialize Gemini client.
        
        Args:
            api_key: Google Gemini API key
        """
        self.api_key = api_key
        if not api_key:
            raise ValueError("Gemini API key is required")
            
        genai.configure(api_key=api_key)
        # Using gemini-2.0-flash-exp or gemini-1.5-flash or gemini-pro
        # Fallback to gemini-pro if flash not available
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
    def generate_response(self, prompt: str) -> str:
        """
        Generate a response using Gemini.
        
        Args:
            prompt: User prompt/question with context already formatted
            
        Returns:
            Generated response string
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            raise e
    
    def generate_streaming_response(self, prompt: str):
        """
        Generate a streaming response using Gemini.
        
        Args:
            prompt: User prompt/question
            
        Yields:
            Response chunks as they are generated
        """
        try:
            response = self.model.generate_content(prompt, stream=True)
            for chunk in response:
                yield chunk.text
        except Exception as e:
            logger.error(f"Gemini streaming failed: {e}")
            raise e
    
    def generate_mind_map(self, context_text: str, mode: str = "architect") -> dict:
        """
        Generate a JSON mind map curriculum (Outline Only) based on the selected mode.
        Returns: { "content": str, "usage": dict }
        """
        from app.llm.prompts import OUTLINE_PROMPTS
        
        # Get prompt for mode, fallback to architect if unknown
        prompt_template = OUTLINE_PROMPTS.get(mode, OUTLINE_PROMPTS["architect"])
        
        prompt = prompt_template.format(context=context_text)
        try:
             response = self.model.generate_content(prompt)
             usage = {
                 "prompt_tokens": response.usage_metadata.prompt_token_count,
                 "completion_tokens": response.usage_metadata.candidates_token_count,
                 "total_tokens": response.usage_metadata.total_token_count
             }
             return {"content": response.text, "usage": usage}
        except Exception as e:
            logger.error(f"Mind Map generation failed: {e}")
            return {"content": "[]", "usage": {}}

    def generate_phase_content(self, context_text: str, title: str, description: str) -> dict:
        """
        Generate detailed content for a specific phase.
        Returns: { "content": str, "usage": dict }
        """
        from app.llm.prompts import PHASE_DETAIL_PROMPT
        
        prompt = PHASE_DETAIL_PROMPT.format(context=context_text, title=title, description=description)
        try:
             response = self.model.generate_content(prompt)
             usage = {
                 "prompt_tokens": response.usage_metadata.prompt_token_count,
                 "completion_tokens": response.usage_metadata.candidates_token_count,
                 "total_tokens": response.usage_metadata.total_token_count
             }
             return {"content": response.text, "usage": usage}
        except Exception as e:
            logger.error(f"Phase generation failed: {e}")
            return {"content": "Failed to generate content.", "usage": {}}
