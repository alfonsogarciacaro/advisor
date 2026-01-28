from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any, List, Optional
from app.services.portfolio_optimizer import PortfolioOptimizerService
from app.core.dependencies import get_portfolio_optimizer_service, get_storage_service
from app.services.storage_service import StorageService
from app.models.portfolio import OptimizationRequest, OptimizationResult

router = APIRouter()

@router.post("/optimize", response_model=Dict[str, str])
async def optimize_portfolio(
    request: OptimizationRequest,
    optimizer_service: PortfolioOptimizerService = Depends(get_portfolio_optimizer_service)
):
    """
    Trigger a portfolio optimization.
    Returns a job_id to track the progress.
    """
    try:
        job_id = await optimizer_service.start_optimization(
            amount=request.amount,
            currency=request.currency,
            excluded_tickers=request.excluded_tickers
        )
        return {"job_id": job_id, "status": "queued"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/optimize/{job_id}", response_model=OptimizationResult)
async def get_optimization_status(
    job_id: str,
    storage_service: StorageService = Depends(get_storage_service)
):
    """
    Get the status and result of a portfolio optimization job.
    """
    job_data = await storage_service.get("optimization_jobs", job_id)
    if not job_data:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job_data
