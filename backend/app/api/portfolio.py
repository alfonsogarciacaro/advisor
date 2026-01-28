from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Optional
from app.services.portfolio_optimizer import PortfolioOptimizerService
from app.core.dependencies import get_portfolio_optimizer_service, get_storage_service, get_logger
from app.services.storage_service import StorageService
from app.services.logger_service import LoggerService
from app.models.portfolio import OptimizationRequest, OptimizationResult
from app.core.utils import sanitize_numpy

router = APIRouter()

@router.post("/optimize", response_model=Dict[str, str])
async def optimize_portfolio(
    request: OptimizationRequest,
    optimizer_service: PortfolioOptimizerService = Depends(get_portfolio_optimizer_service),
    logger: LoggerService = Depends(get_logger)
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
    storage_service: StorageService = Depends(get_storage_service),
    logger: LoggerService = Depends(get_logger)
):
    """
    Get the status and result of a portfolio optimization job.
    """
    job_data = await storage_service.get("optimization_jobs", job_id)
    if not job_data:
        raise HTTPException(status_code=404, detail="Job not found")

    return sanitize_numpy(job_data)


@router.delete("/optimize/cache")
async def clear_optimization_cache(
    job_id: Optional[str] = Query(None, description="Specific job ID to clear, or omit to clear all"),
    storage_service: StorageService = Depends(get_storage_service),
    logger: LoggerService = Depends(get_logger)
):
    """
    Clear cached optimization data. Either clears a specific job or all jobs.
    """
    collection = "optimization_jobs"

    if job_id:
        # Delete specific job
        await storage_service.delete(collection, job_id)
        logger.info(f"Cleared optimization cache for job {job_id}")
        return {"message": f"Cleared cache for job {job_id}", "jobs_cleared": 1}
    else:
        # Delete all jobs (this requires listing them first - implementation depends on storage service)
        # For now, return a message that this feature requires listing capability
        logger.info(f"Cache clear requested for all jobs")
        return {"message": "Clearing all jobs requires storage service list capability", "jobs_cleared": 0}
