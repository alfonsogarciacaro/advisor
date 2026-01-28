import asyncio
import sys
import os
import logging
from typing import Dict, Any, List, Optional

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.dependencies import get_agent_service, get_llm_service
from app.services.llm_service import MockLLMProvider
from unittest.mock import MagicMock
from app.services.storage_service import StorageService

# Mock Storage Service to avoid Firestore auth
class MockStorage(StorageService):
    async def save(self, collection: str, key: str, data: Dict[str, Any]):
        pass
    async def get(self, collection: str, key: str) -> Optional[Dict[str, Any]]:
        return None
    async def delete(self, collection: str, key: str):
        pass
    async def list_all(self, collection: str) -> List[Dict[str, Any]]:
        return []
    async def list(self, collection: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        return []
    async def update(self, collection: str, key: str, data: Dict[str, Any]):
        pass

# Patch dependencies
import app.core.dependencies
app.core.dependencies.get_storage_service = lambda: MockStorage()

from app.core.dependencies import (
    get_agent_service, get_llm_service, get_config_service,
    get_news_service, get_history_service, get_forecasting_engine,
    get_macro_service, get_risk_calculator
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_research_agent():
    print("--- Verifying Research Agent Flow ---")
    
    # Initialize dependencies manually to avoid FastAPI Depends() issues
    print("Initializing services...")
    config_service = get_config_service()
    news_service = get_news_service()
    history_service = get_history_service()
    llm_service = get_llm_service()
    forecasting_engine = get_forecasting_engine()
    macro_service = get_macro_service()
    risk_calculator = get_risk_calculator()
    
    print("Initializing AgentService...")
    agent_service = get_agent_service(
        news_service=news_service,
        history_service=history_service,
        llm_service=llm_service,
        forecasting_engine=forecasting_engine,
        macro_service=macro_service,
        risk_calculator=risk_calculator,
        config_service=config_service
    )
    
    # Check if research agent is registered
    if "research" not in agent_service._agents:
        print("ERROR: Research Agent not registered!")
        return

    print("Agent registered successfully.")
    
    # Instantiate the agent manually for testing (bypassing AgentService.execute_run)
    # The registered class has dependencies bound in closure
    agent_cls = agent_service._agents["research"]
    # We use MockStorage here again
    agent = agent_cls(logger, MockStorage())
    
    input_query = "What is the outlook for SPY?"
    print(f"Running agent with query: {input_query}")
    
    try:
        # Run the graph
        result = await agent.run("test-run-id", input_query)
        
        # Check outputs
        print("\n--- Agent Execution Result ---")
        
        # Check Scenarios (LLM Step)
        scenarios = result.get("scenarios", {})
        if scenarios:
             print(f"✅ Scenarios generated: {list(scenarios.keys())}")
             if "GLOBAL" in scenarios:
                 print(f"   GLOBAL cases: {list(scenarios['GLOBAL'].keys())}")
        else:
             print("❌ No scenarios generated.")
             
        # Check Refined Forecasts (Forecasting Engine Step)
        refined = result.get("refined_forecasts", {})
        if refined:
             print(f"✅ Refined forecasts generated for cases: {list(refined.keys())}")
        else:
             print("❌ No refined forecasts generated (Note: this might happen if no market data is available in env).")

        # Check Summary
        summary = result.get("summary", "")
        if summary:
             print("✅ Summary generated.")
             print("--- Summary Preview ---")
             print(summary[:200] + "...")
        else:
             print("❌ No summary generated.")
             
    except Exception as e:
        print(f"❌ Error running agent: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_research_agent())
