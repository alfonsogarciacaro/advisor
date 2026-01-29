from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union

# Import existing models
from app.models.portfolio import PortfolioAsset, OptimizationResult, ScenarioForecast

class RiskProfile(str, Enum):
    """Risk tolerance levels for long-term family investors"""
    VERY_CONSERVATIVE = "very_conservative"  # Max capital preservation, accept lower returns
    CONSERVATIVE = "conservative"  # Focus on stability, some growth
    MODERATE = "moderate"  # Balanced approach
    GROWTH = "growth"  # Accept higher volatility for better returns
    AGGRESSIVE = "aggressive"  # Maximum growth acceptance

class InvestmentFrequency(str, Enum):
    """Recurring investment frequency options"""
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"

class TaxAccountType(str, Enum):
    """Tax-advantaged account types, primarily for Japanese market"""
    TAXABLE = "taxable"  # Ordinary taxable account
    NISA_GENERAL = "nisa_general"  # New NISA (General Account)
    NISA_GROWTH = "nisa_growth"  # New NISA (Growth Account)
    IDECO = "ideco"  # iDeCo (Individual Defined Contribution pension)
    DC_PENSION = "dc_pension"  # Company DC pension
    OTHER = "other"  # Other country-specific accounts

class TaxAccount(BaseModel):
    """Configuration for a tax-advantaged account"""
    account_type: TaxAccountType
    name: str  # User-defined name for the account
    annual_limit: Optional[float] = None  # Annual contribution limit (e.g., 1.2M JPY for NISA General)
    current_balance: float = 0.0
    available_space: float = 0.0  # Remaining space for this year
    withdrawal_rules: Optional[str] = None  # Description of withdrawal restrictions

    # Tax configuration
    dividend_tax_rate: float = 0.0  # 0% for NISA/iDeCo
    capital_gains_tax_rate: float = 0.0  # 0% for NISA/iDeCo
    contribution_deductible: bool = False  # True for iDeCo

class RecurringInvestment(BaseModel):
    """Recurring investment (DCA) configuration"""
    enabled: bool = False
    frequency: InvestmentFrequency = InvestmentFrequency.MONTHLY
    amount: float = Field(..., gt=0, description="Amount to invest each period")
    currency: str = "JPY"
    dividend_reinvestment: bool = True  # Automatically reinvest dividends
    next_investment_date: Optional[datetime] = None

class ResearchRun(BaseModel):
    """A single research agent execution within a plan"""
    run_id: str
    timestamp: datetime
    query: str
    result_summary: str
    scenarios: Optional[List[ScenarioForecast]] = None
    refined_forecasts: Optional[Dict[str, Any]] = None
    follow_up_suggestions: Optional[List[str]] = None

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

class Plan(BaseModel):
    """
    An investment plan representing a user's portfolio strategy.

    A plan can start from scratch (new investment) or from an existing portfolio.
    It contains the optimization results, research history, and configuration.
    """
    plan_id: str
    user_id: str  # Future: Will be used for multi-user support
    name: str  # User-defined plan name
    description: Optional[str] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime

    # Portfolio Configuration
    risk_preference: RiskProfile = RiskProfile.MODERATE

    # Initial State (can be empty for new investments)
    initial_portfolio: Optional[List[PortfolioAsset]] = None  # Existing holdings
    initial_amount: Optional[float] = None  # Cash amount to invest

    # Optimization Results
    optimization_result: Optional[OptimizationResult] = None

    # Recurring Investment Settings
    recurring_investment: Optional[RecurringInvestment] = None

    # Tax Configuration
    tax_accounts: Optional[List[TaxAccount]] = None

    # Portfolio Constraints
    constraints: Optional[PortfolioConstraints] = None

    # Research History
    research_history: List[ResearchRun] = []

    # User Notes
    notes: Optional[str] = None
