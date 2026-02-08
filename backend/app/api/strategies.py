from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Dict, Any, Optional
from app.services.config_service import ConfigService
from app.core.dependencies import get_config_service, get_logger, get_current_user
from app.services.logger_service import LoggerService
from app.models.auth import User
import yaml
from pathlib import Path

router = APIRouter()

# Load strategies config
STRATEGIES_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "strategies_config.yaml"


def _load_strategies_config() -> Dict[str, Any]:
    """Load the strategies configuration from YAML file."""
    try:
        with open(STRATEGIES_CONFIG_PATH, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        # Return default config if file doesn't exist
        return {
            "strategies": [],
            "tax_settings": {
                "short_term_capital_gains_rate": 0.35,
                "long_term_capital_gains_rate": 0.15,
                "account_types": {}
            }
        }


@router.get("/strategies", response_model=List[Dict[str, Any]])
async def list_strategies(
    risk_level: Optional[str] = Query(None, description="Filter by risk level (conservative, moderate, aggressive)"),
    current_user: User = Depends(get_current_user),
    config_service: ConfigService = Depends(get_config_service),
    logger: LoggerService = Depends(get_logger)
):
    """
    List all available strategy templates.
    Can optionally filter by risk level.
    """
    config = _load_strategies_config()
    strategies = config.get("strategies", [])

    # Filter by risk level if provided
    if risk_level:
        strategies = [s for s in strategies if s.get("risk_level") == risk_level]

    return strategies


@router.get("/strategies/{strategy_id}", response_model=Dict[str, Any])
async def get_strategy(
    strategy_id: str,
    current_user: User = Depends(get_current_user),
    logger: LoggerService = Depends(get_logger)
):
    """
    Get details of a specific strategy template.
    """
    config = _load_strategies_config()
    strategies = config.get("strategies", [])

    for strategy in strategies:
        if strategy.get("strategy_id") == strategy_id:
            return strategy

    raise HTTPException(status_code=404, detail=f"Strategy '{strategy_id}' not found")


@router.get("/config/tax-settings", response_model=Dict[str, Any])
async def get_tax_settings(
    current_user: User = Depends(get_current_user),
    logger: LoggerService = Depends(get_logger)
):
    """
    Get tax settings for different account types.
    """
    config = _load_strategies_config()
    tax_settings = config.get("tax_settings", {})
    return tax_settings
