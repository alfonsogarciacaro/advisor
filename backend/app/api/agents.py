from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from app.services.agent_service import AgentService
from app.core.dependencies import get_agent_service, get_logger
from app.services.logger_service import LoggerService

router = APIRouter()

class AgentRunRequest(BaseModel):
    input: Any

class AgentRunResponse(BaseModel):
    run_id: str
    status: str

@router.post("/{agent_name}/run", response_model=AgentRunResponse)
async def run_agent(
    agent_name: str, 
    request: AgentRunRequest,
    background_tasks: BackgroundTasks,
    agent_service: AgentService = Depends(get_agent_service),
    logger: LoggerService = Depends(get_logger)
):
    try:
        run_id = await agent_service.create_run(agent_name, request.input)
        
        background_tasks.add_task(
            agent_service.execute_run, 
            run_id=run_id, 
            agent_name=agent_name, 
            input_data=request.input
        )
        
        return AgentRunResponse(run_id=run_id, status="queued")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/runs/{run_id}")
async def get_run_status(
    run_id: str,
    agent_service: AgentService = Depends(get_agent_service),
    logger: LoggerService = Depends(get_logger)
):
    run = await agent_service.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run

@router.get("/runs/{run_id}/logs")
async def get_run_logs(
    run_id: str,
    agent_service: AgentService = Depends(get_agent_service)
):
    logs = await agent_service.get_run_logs(run_id)
    return logs
