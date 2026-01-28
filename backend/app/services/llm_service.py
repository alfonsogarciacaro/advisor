import os
import hashlib
import json
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import google.generativeai as genai
from app.services.config_service import ConfigService
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)

class LLMProvider(ABC):
    @abstractmethod
    async def generate_content(self, prompt: str) -> str:
        pass

class MockLLMProvider(LLMProvider):
    async def generate_content(self, prompt: str) -> str:
        logger.info(f"Mock LLM received prompt: {prompt[:50]}...")
        # Return a valid JSON string for scenario generation if it detects it's being asked for JSON
        if "json" in prompt.lower():
            return """
            {
                "scenarios": {
                    "SPY": {
                        "base_case": {"weight": 0.6, "drift_adj": 0.0, "vol_adj": 0.0, "description": "Steady growth"},
                        "bull_case": {"weight": 0.2, "drift_adj": 0.05, "vol_adj": -0.1, "description": "High growth"},
                        "bear_case": {"weight": 0.2, "drift_adj": -0.1, "vol_adj": 0.2, "description": "Recession"}
                    }
                }
            }
            """
        return "Mock LLM Response: This is a simulated response."

class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    async def generate_content(self, prompt: str) -> str:
        try:
            # Run in executor to avoid blocking event loop
            import asyncio
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            raise e

class LLMService:
    def __init__(self, config_service: ConfigService, storage_service: StorageService):
        self.config_service = config_service
        self.storage_service = storage_service
        self.collection = "llm_cache"
        self.provider: LLMProvider = self._initialize_provider()

    def _initialize_provider(self) -> LLMProvider:
        settings = self.config_service.get_llm_settings()
        provider_type = settings.get("provider", "gemini")
        
        # Check environment variable for API key
        api_key = os.getenv("GEMINI_API_KEY")
        
        if provider_type == "gemini" and api_key:
            logger.info("Initializing Gemini LLM Provider")
            return GeminiProvider(api_key=api_key)
        else:
            logger.warning("Gemini API key not found or provider not set to gemini. Using Mock Provider.")
            return MockLLMProvider()

    def _generate_cache_key(self, prompt: str) -> str:
        """Generate a deterministic cache key for the prompt."""
        return hashlib.md5(prompt.encode('utf-8')).hexdigest()

    async def generate_response(self, prompt: str, use_cache: bool = True) -> str:
        """
        Generate a response from the LLM, using cache if enabled.
        """
        if use_cache:
            cache_key = self._generate_cache_key(prompt)
            cached_entry = await self.storage_service.get(self.collection, cache_key)
            if cached_entry:
                logger.info("Returning cached LLM response")
                return cached_entry.get("response", "")

        try:
            response = await self.provider.generate_content(prompt)
            
            if use_cache:
                cache_key = self._generate_cache_key(prompt)
                await self.storage_service.save(self.collection, cache_key, {"response": response, "prompt": prompt})
                
            return response
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            return ""

    async def generate_json(self, prompt: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Generate a response and attempt to parse it as JSON.
        Adds formatting instructions to the prompt if not present.
        """
        json_prompt = prompt
        if "json" not in prompt.lower():
            json_prompt += "\n\nPlease provide the output in valid JSON format."
            
        response_text = await self.generate_response(json_prompt, use_cache)
        
        # Clean up code blocks if present (markdown formatting)
        clean_text = response_text.replace("```json", "").replace("```", "").strip()
        
        try:
            return json.loads(clean_text)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON from LLM response: {clean_text[:100]}...")
            return {}
