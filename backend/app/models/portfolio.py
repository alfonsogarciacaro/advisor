from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from app.models.plan import PortfolioConstraints

class OptimizationRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Investment amount")
    currency: str = Field(default="USD", description="Investment currency")
    risk_tolerance: Optional[float] = Field(None, ge=0, le=1, description="Risk tolerance (0-1), optional")
    excluded_tickers: Optional[List[str]] = Field(default=[], description="List of tickers to exclude from optimization")
    plan_id: Optional[str] = Field(None, description="Plan ID to get constraints from")
    constraints: Optional[Dict[str, Any]] = None  # Forward reference to PortfolioConstraints
    fast: Optional[bool] = Field(False, description="Use fast mode (skip forecasting, LLM, reduce simulations) for testing")

class PortfolioAsset(BaseModel):
    ticker: str
    weight: float
    amount: float
    shares: float
    price: float
    expected_return: Optional[float] = None
    annual_expense_ratio: Optional[float] = None
    contribution_to_risk: Optional[float] = None

class EfficientFrontierPoint(BaseModel):
    annual_volatility: Optional[float] = None
    annual_return: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    weights: Dict[str, float]

class ScenarioForecast(BaseModel):
    name: str
    probability: float
    description: str
    expected_portfolio_value: Optional[float] = None
    expected_return: Optional[float] = None
    annual_volatility: Optional[float] = None
    trajectory: Optional[List[Dict[str, Any]]] = None

class OptimizationResult(BaseModel):
    job_id: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    initial_amount: float
    currency: str
    optimal_portfolio: Optional[List[PortfolioAsset]] = None
    efficient_frontier: Optional[List[EfficientFrontierPoint]] = None
    metrics: Optional[Dict[str, Optional[float]]] = None
    scenarios: Optional[List[ScenarioForecast]] = None
    llm_report: Optional[str] = None
    error: Optional[str] = None
