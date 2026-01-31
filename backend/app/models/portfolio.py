from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime

# Import shared types
from app.models.types import TaxAccountType


class AssetHolding(BaseModel):
    """User's existing asset holding with account information"""
    ticker: str = Field(..., description="ETF ticker symbol")
    account_type: TaxAccountType = Field(..., description="Which account holds this asset")
    monetary_value: float = Field(..., gt=0, description="Value in BASE currency (e.g., JPY for Japan residents)")
    # Note: No currency field - always in plan's base_currency


class PortfolioEditRequest(BaseModel):
    """Request to edit plan's initial portfolio"""
    initial_portfolio: List[AssetHolding]
    # No currency field - uses plan's base_currency


class ValidationError(BaseModel):
    """Single validation error"""
    account_type: str = Field(..., description="Account type with the error")
    message: str = Field(..., description="Error message")
    total: Optional[float] = Field(None, description="Total value in account")
    limit: Optional[float] = Field(None, description="Account limit")


class ValidationResult(BaseModel):
    """Result of portfolio validation"""
    valid: bool = Field(..., description="Whether the portfolio is valid")
    errors: List[ValidationError] = Field(default_factory=list, description="List of validation errors")
    warnings: List[Dict[str, str]] = Field(default_factory=list, description="List of warnings")


class PortfolioValidationRequest(BaseModel):
    """Request to validate portfolio holdings"""
    plan_id: str
    holdings: List[AssetHolding]


class PortfolioConstraints(BaseModel):
    """
    Constraints for portfolio optimization to prevent flawed allocations.

    Allows users and LLM to guide the optimization toward more practical
    portfolios by limiting concentrations, sector exposure, and ensuring
    diversification.
    """
    # Asset-level constraints
    max_asset_weight: Optional[float] = Field(None, ge=0, le=1, description="Maximum weight for any single asset (e.g., 0.20 for max 20%)")
    excluded_assets: List[str] = Field(default_factory=list, description="Assets to exclude from optimization")

    # Sector/asset class constraints
    sector_constraints: Dict[str, Dict[str, float]] = Field(
        default_factory=dict,
        description="Sector-level constraints e.g., {'Technology': {'max': 0.30}, 'Bonds': {'min': 0.10}}"
    )

    # Diversification constraints
    min_holdings: int = Field(3, ge=1, le=50, description="Minimum number of holdings")
    max_holdings: int = Field(20, ge=1, le=100, description="Maximum number of holdings")

    # Practical constraints
    min_position_size: float = Field(0.01, ge=0, le=1, description="Minimum position size (1% default to avoid dust)")

    # Risk constraints
    max_volatility: Optional[float] = Field(None, ge=0, le=1, description="Maximum portfolio volatility")
    max_drawdown: Optional[float] = Field(None, ge=0, le=1, description="Maximum acceptable drawdown")

    # LLM-suggested guidelines
    llm_guidelines: List[str] = Field(default_factory=list, description="Constraints suggested by LLM analysis")

    # Metadata
    last_applied_at: Optional[datetime] = None
    generated_from: Optional[str] = Field(None, description="Where these constraints came from (user/llm)")


class OptimizationRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Investment amount")
    currency: str = Field(default="USD", description="Investment currency")
    risk_tolerance: Optional[float] = Field(None, ge=0, le=1, description="Risk tolerance (0-1), optional")
    excluded_tickers: Optional[List[str]] = Field(default=[], description="List of tickers to exclude from optimization")
    plan_id: Optional[str] = Field(None, description="Plan ID to get constraints from")
    constraints: Optional[PortfolioConstraints] = None
    historical_date: Optional[str] = Field(None, description="Historical date for backtesting (YYYY-MM-DD)")
    use_strategy: Optional[str] = Field(None, description="Strategy template to use (e.g., 'conservative_income')")
    account_type: Optional[str] = Field(None, description="Account type for tax calculations (e.g., 'taxable', 'nisa_growth')")
    end_date: Optional[str] = Field(None, description="End date for backtesting (YYYY-MM-DD)")

class PortfolioAsset(BaseModel):
    ticker: str
    weight: float
    amount: float
    shares: float
    price: float
    expected_return: Optional[float] = None
    annual_expense_ratio: Optional[float] = None
    contribution_to_risk: Optional[float] = None
    account_type: Optional[TaxAccountType] = None  # Track which account holds the asset

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
    backtest_result: Optional["BacktestResult"] = None


class BacktestResult(BaseModel):
    """Results from historical backtest showing how a strategy would have performed"""

    # Portfolio trajectory over time
    trajectory: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Historical portfolio values [{'date': '2020-01-01', 'value': 10000}, ...]"
    )

    # Benchmark trajectory (60/40 SPY/AGG)
    benchmark_trajectory: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Benchmark portfolio values for comparison"
    )

    # Performance metrics
    metrics: Dict[str, float] = Field(
        default_factory=dict,
        description="Performance metrics (total_return, max_drawdown, sharpe_ratio, etc.)"
    )

    # Historical context
    start_date: Optional[str] = Field(None, description="Backtest start date (ISO format)")
    end_date: Optional[str] = Field(None, description="Backtest end date (ISO format)")

    # Tax information (if applicable)
    account_type: Optional[str] = Field(None, description="Account type used (taxable, nisa_growth, etc.)")
    capital_gains_tax: Optional[float] = Field(None, description="Capital gains tax paid")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "trajectory": [
                    {"date": "2020-01-01", "value": 10000},
                    {"date": "2020-03-23", "value": 7500},  # COVID crash
                    {"date": "2020-12-31", "value": 11500}
                ],
                "benchmark_trajectory": [
                    {"date": "2020-01-01", "value": 10000},
                    {"date": "2020-12-31", "value": 10800}
                ],
                "metrics": {
                    "total_return": 0.15,
                    "pre_tax_total_return": 0.18,
                    "max_drawdown": -0.25,
                    "recovery_days": 180,
                    "volatility": 0.18,
                    "sharpe_ratio": 0.85,
                    "cagr": 0.14,
                    "final_value": 11500,
                    "tax_rate": 0.15,
                    "tax_impact": 0.03
                },
                "start_date": "2020-01-01",
                "end_date": "2020-12-31",
                "account_type": "taxable",
                "capital_gains_tax": 300.0
            }
        }
    )
