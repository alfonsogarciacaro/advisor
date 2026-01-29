import os
import hashlib
import json
import logging
import asyncio
import google.genai as genai
from openai import OpenAI
from langchain.chat_models import BaseChatModel
from langchain.agents import create_agent
from langchain_core.tools import BaseTool
from abc import ABC, abstractmethod
from typing import Dict, Any, TypeVar, Optional, List
from app.services.config_service import ConfigService
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)

T = TypeVar('T')

def run_agent_with_logging(llm: BaseChatModel, tools: List[BaseTool], prompt: str) -> str:
    agent = create_agent(llm, tools)
    final_response = ""
    for chunk in agent.stream({"messages": [{"role": "user", "content": prompt}]}, stream_mode="values"):
        # Each chunk contains the full state at that point
        msg = chunk["messages"][-1]
        if msg.type == "human":
            continue 
        if msg.content:
            if isinstance(msg.content, str):
                step_text = msg.content
            elif isinstance(msg.content, list):
                # If we want to include thoughts, we need to add block.get("type") == "thought"
                step_text = "".join([block.get("text", "") for block in msg.content if isinstance(block, dict) and block.get("type") == "text"])
            else:
                step_text = ""
            final_response = step_text
            logger.info(f"LLM message: {step_text}")
        elif msg.tool_calls:
            logger.info(f"LLM tool calls: {[tc['name'] for tc in msg.tool_calls]}")

    return final_response

class LLMProvider(ABC):
    @abstractmethod
    async def generate_content(self, prompt: str, tools: Optional[List[BaseTool]] = None) -> str | None:
        pass

class MockLLMProvider(LLMProvider):
    async def generate_content(self, prompt: str, tools: Optional[List[BaseTool]] = None) -> str | None:
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
    def __init__(self, api_key: str, model_name: str = "gemini-3-flash-preview"):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    async def generate_content(self, prompt: str, tools: Optional[List[BaseTool]] = None) -> str | None:
        if tools:
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(client=self.client, model=self.model_name)
            response = await asyncio.to_thread(run_agent_with_logging, llm=llm, tools=tools, prompt=prompt)
            return response
        else:
            response = await asyncio.to_thread(self.client.models.generate_content, model=self.model_name, contents=[prompt])
            return response.text

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model_name: str, base_url: str):
        self.model_name = model_name
        self.client = OpenAI(base_url=base_url, api_key=api_key)

    async def generate_content(self, prompt: str, tools: Optional[List[BaseTool]] = None) -> str | None:
        if tools:
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(client=self.client, model=self.model_name)
            response = await asyncio.to_thread(run_agent_with_logging, llm=llm, tools=tools, prompt=prompt)
            return response
            # Convert LangChain tools to OpenAI format
            # from langchain_core.utils.function_calling import convert_to_openai_tool
            # openai_tools = [convert_to_openai_tool(t) for t in tools]
            # response = await asyncio.to_thread(self.client.chat.completions.create, model=self.model_name, messages=messages, tools=openai_tools)
        else:
            response = await asyncio.to_thread(self.client.chat.completions.create, model=self.model_name, messages=[{"role": "user", "content": prompt}])
            return response.choices[0].message.content

class LLMService:
    def __init__(self, config_service: ConfigService, storage_service: StorageService):
        self.config_service = config_service
        self.storage_service = storage_service
        self.collection = "llm_cache"
        self.provider: LLMProvider = self._initialize_provider()

    def _initialize_provider(self) -> LLMProvider:
        # api_key = os.getenv("OPENAI_API_KEY")
        # base_url = os.getenv("OPENAI_BASE_URL")
        # model_name = os.getenv("OPENAI_MODEL_NAME")
        # if api_key and base_url and model_name:
        #     logger.info("Initializing OpenAI LLM Provider")
        #     return OpenAIProvider(api_key=api_key, model_name=model_name, base_url=base_url)

        api_key = os.getenv("GEMINI_API_KEY")        
        if api_key:
            logger.info("Initializing Gemini LLM Provider")
            return GeminiProvider(api_key=api_key)

        logger.warning("No API key found. Using Mock Provider.")
        return MockLLMProvider()

    def _generate_cache_key(self, prompt: str) -> str:
        """Generate a deterministic cache key for the prompt."""
        return hashlib.md5(prompt.encode('utf-8')).hexdigest()

    async def generate_response(self, prompt: str, use_cache: bool = True, tools: Optional[List[BaseTool]] = None) -> str:
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
            response = await self.provider.generate_content(prompt, tools=tools)
            
            if use_cache and response is not None:
                cache_key = self._generate_cache_key(prompt)
                await self.storage_service.save(self.collection, cache_key, {"response": response, "prompt": prompt})
                
            return response or ""
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
