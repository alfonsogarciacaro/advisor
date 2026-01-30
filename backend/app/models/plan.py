from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union

# Import shared types
from app.models.types import RiskProfile, TaxAccountType
from app.models.portfolio import (
    PortfolioConstraints,
    AssetHolding,
    OptimizationResult,
    ScenarioForecast
)

class InvestmentFrequency(str, Enum):
    """Recurring investment frequency options"""
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"

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

    # Currency Configuration
    base_currency: str = "JPY"  # Base currency for all values (auto from tax residence)

    # Portfolio Configuration
    risk_preference: RiskProfile = RiskProfile.MODERATE

    # Initial State (can be empty for new investments)
    initial_portfolio: Optional[List[AssetHolding]] = None
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
