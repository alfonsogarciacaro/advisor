from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class OptimizationRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Investment amount")
    currency: str = Field(default="USD", description="Investment currency")
    risk_tolerance: Optional[float] = Field(None, ge=0, le=1, description="Risk tolerance (0-1), optional")
    excluded_tickers: Optional[List[str]] = Field(default=[], description="List of tickers to exclude from optimization")

class PortfolioAsset(BaseModel):
    ticker: str
    weight: float
    amount: float
    shares: float
    price: float
    expected_return: float
    contribution_to_risk: float

class EfficientFrontierPoint(BaseModel):
    annual_volatility: float
    annual_return: float
    sharpe_ratio: float
    weights: Dict[str, float]

class OptimizationResult(BaseModel):
    job_id: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    initial_amount: float
    currency: str
    optimal_portfolio: Optional[List[PortfolioAsset]] = None
    efficient_frontier: Optional[List[EfficientFrontierPoint]] = None
    metrics: Optional[Dict[str, float]] = None
    error: Optional[str] = None
