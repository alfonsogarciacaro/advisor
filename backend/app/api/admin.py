from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from app.core.dependencies import get_config_service, get_current_admin_user, get_storage_service
from app.services.config_service import ConfigService
from app.services.storage_service import StorageService
from app.models.auth import User

router = APIRouter()

@router.get("/config")
async def get_admin_config(
    current_user: User = Depends(get_current_admin_user),
    config_service: ConfigService = Depends(get_config_service)
) -> Dict[str, Any]:
    """Get all admin-level configuration"""
    return await config_service.get_all_config()

@router.put("/config/etfs")
async def update_etf_config(
    new_config: Dict[str, Any],
    current_user: User = Depends(get_current_admin_user),
    config_service: ConfigService = Depends(get_config_service)
):
    """Update ETF configuration"""
    await config_service.update_etf_config(new_config)
    return {"status": "updated", "config_type": "etfs"}

@router.put("/config/forecasting")
async def update_forecasting_config(
    new_config: Dict[str, Any],
    current_user: User = Depends(get_current_admin_user),
    config_service: ConfigService = Depends(get_config_service)
):
    """Update forecasting configuration"""
    await config_service.update_forecasting_config(new_config)
    return {"status": "updated", "config_type": "forecasting"}

@router.post("/config/reset")
async def reset_config_to_defaults(
    current_user: User = Depends(get_current_admin_user),
    config_service: ConfigService = Depends(get_config_service)
):
    """Reset all configuration to YAML defaults"""
    await config_service.reset_to_defaults()
    return {"status": "reset", "message": "Configuration reset to YAML defaults"}

@router.get("/cache/stats")
async def get_cache_stats(
    current_user: User = Depends(get_current_admin_user),
    storage_service: StorageService = Depends(get_storage_service)
) -> Dict[str, Any]:
    """Get cache statistics"""
    # Get counts for various cached collections
    stats = {}
    
    collections = ["news_cache", "historical_data", "optimization_jobs", "agent_runs", "plans"]
    
    for collection in collections:
        try:
            items = await storage_service.list_all(collection)
            stats[collection] = {
                "count": len(items),
                "collection": collection
            }
        except Exception as e:
            stats[collection] = {
                "count": 0,
                "error": str(e)
            }
    
    return stats

@router.delete("/cache/{cache_type}")
async def clear_cache(
    cache_type: str,
    current_user: User = Depends(get_current_admin_user),
    storage_service: StorageService = Depends(get_storage_service)
):
    """Clear specific cache type"""
    valid_caches = ["news_cache", "historical_data", "optimization_jobs", "agent_runs"]
    
    if cache_type not in valid_caches:
        raise HTTPException(status_code=400, detail=f"Invalid cache type. Must be one of: {valid_caches}")
    
    # Get all items and delete them
    try:
        items = await storage_service.list_all(cache_type)
        count = 0
        for item in items:
            # Extract ID from item - could be under different keys
            item_id = item.get("id") or item.get("job_id") or item.get("run_id") or item.get("plan_id")
            if item_id:
                await storage_service.delete(cache_type, item_id)
                count += 1
        
        return {"status": "cleared", "cache_type": cache_type, "items_deleted": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {str(e)}")
