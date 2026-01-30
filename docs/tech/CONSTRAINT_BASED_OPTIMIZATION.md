# Portfolio Optimization Constraints

## Problem

The current Mean-Variance Optimization (MVO) is purely mathematical and may produce allocations that are:
- **Over-concentrated** in single assets (e.g., 40% Gold)
- **Unbalanced** across asset classes
- **Not aligned** with investor preferences
- **Ignoring** practical constraints (liquidity, minimum investment, etc.)

## Solution: Constraint-Based Optimization

Add flexible constraints to the portfolio optimizer that can be:
1. **Configured by user** (in Plan settings)
2. **Suggested by LLM** (after analyzing the optimization)
3. **Applied incrementally** (iterative refinement)

---

## Constraint Types

### 1. Asset-Level Constraints

```python
# Maximum allocation per asset
asset_constraints = {
    "GLD": { "max_weight": 0.10 },  # Max 10% Gold
    "TSLA": { "max_weight": 0.05 }, # Max 5% Tesla
    "BTC":  { "max_weight": 0.00 }, # Exclude crypto
}
```

### 2. Sector/Asset Class Constraints

```python
# Group constraints
sector_constraints = {
    "Technology": { "max_weight": 0.30 },  # Max 30% tech
    "Commodities": { "max_weight": 0.10 }, # Max 10% commodities
    "Bonds": { "min_weight": 0.10 },      # Min 10% bonds
}
```

### 3. Diversification Constraints

```python
# Minimum number of holdings
diversification_constraint = {
    "min_holdings": 5,
    "max_weight_per_holding": 0.25,
}
```

### 4. Practical Constraints

```python
practical_constraints = {
    "min_trade_amount": 5000,    # Minimum $5K per trade
    "min_weight": 0.01,          # Minimum 1% position (avoid dust)
    "round_lots": True,          # Round to whole shares
}
```

---

## Data Model

### Update Plan Model

```python
class PortfolioConstraints(BaseModel):
    """User-defined constraints for portfolio optimization"""

    # Asset-level constraints
    max_asset_weight: Optional[float] = None  # e.g., 0.20 for max 20% any asset
    excluded_assets: List[str] = []           # Assets to exclude

    # Sector/asset class constraints
    sector_constraints: Dict[str, Dict[str, float]] = {}
    # Example: { "Technology": {"max": 0.30}, "Bonds": {"min": 0.10} }

    # Diversification
    min_holdings: int = 3
    max_holdings: int = 20

    # Practical
    min_position_size: float = 0.01  # 1% minimum
    require_even_weighting: bool = False

    # Risk constraints
    max_volatility: Optional[float] = None
    max_drawdown: Optional[float] = None

    # LLM-suggested (from AI analysis)
    llm_guidelines: List[str] = []

class Plan(BaseModel):
    # ... existing fields ...
    constraints: Optional[PortfolioConstraints] = None
```

---

## Optimization Flow with Constraints

### Current Flow
```
User Request → Fetch Data → Forecast Returns → MVO → Result
                                              ↓
                                         (May be flawed)
```

### New Flow
```
User Request → Fetch Data → Forecast Returns → MVO (with constraints) → Result
                                              ↓
                                    Generate AI Report
                                              ↓
                            LLM suggests constraints if issues found
                                              ↓
                         User can adjust constraints & re-optimize
```

---

## User Interface

### 1. Initial Optimization (No Constraints)
```
┌─────────────────────────────────────────┐
│  Portfolio Optimization Result          │
├─────────────────────────────────────────┤
│  SPY: 35%                               │
│  GLD: 40% ← ⚠️ CONCENTRATION RISK      │
│  VEA: 15%                               │
│  VWO: 10%                               │
│                                         │
│  [AI Report] [View Constraints]         │
└─────────────────────────────────────────┘
```

### 2. AI Report Identifies Issue
```
┌─────────────────────────────────────────┐
│  AI Analysis Report                     │
├─────────────────────────────────────────┤
│  The optimization shows 40% allocation  │
│  to Gold (GLD), which may be too        │
│  concentrated for a moderate risk       │
│  profile.                               │
│                                         │
│  [SUGGESTION] Limit Gold to 10%         │
│  [Apply & Re-optimize]                  │
└─────────────────────────────────────────┘
```

### 3. Constraints Panel
```
┌─────────────────────────────────────────┐
│  Portfolio Constraints                  │
├─────────────────────────────────────────┤
│  🎯 Maximum Position Size               │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  20%    │
│  [min: 5%] [max: 30%]                   │
│                                         │
│  🏢 Sector Limits                        │
│  • Commodities: max 10%                 │
│  • Technology: max 30%                  │
│  [+ Add Sector]                         │
│                                         │
│  📊 Diversification                      │
│  • Min holdings: 5                      │
│  • Max holdings: 15                     │
│                                         │
│  🚫 Excluded Assets                      │
│  [Remove]                               │
│                                         │
│  [Re-optimize with Constraints]         │
└─────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Backend Enhancement

#### Update `portfolio_optimizer.py`

```python
def _calculate_mean_variance_constrained(
    self,
    mean_returns: pd.Series,
    cov_matrix: pd.DataFrame,
    constraints: PortfolioConstraints
) -> Tuple[List[EfficientFrontierPoint], Dict[str, Any]]:
    """
    MVO with user-specified constraints.
    """
    num_assets = len(mean_returns)
    tickers = mean_returns.index.tolist()

    # Build constraint list
    constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
    bounds = tuple((0.0, 1.0) for asset in range(num_assets))

    # Add asset-level max weight constraint
    if constraints.max_asset_weight:
        for i in range(num_assets):
            bounds[i] = (0.0, constraints.max_asset_weight)

    # Add excluded assets
    excluded_indices = [
        i for i, ticker in enumerate(tickers)
        if ticker in constraints.excluded_assets
    ]
    for i in excluded_indices:
        bounds[i] = (0.0, 0.0)

    # Add sector constraints (if sector mapping available)
    if constraints.sector_constraints:
        # Need sector mapping from config
        sector_map = self.config_service.get_sector_mapping()
        for sector, limits in constraints.sector_constraints.items():
            sector_indices = [
                i for i, ticker in enumerate(tickers)
                if sector_map.get(ticker) == sector
            ]
            if 'max' in limits:
                constraints.append({
                    'type': 'ineq',
                    'fun': lambda x, idx=sector_indices: limits['max'] - np.sum(x[idx])
                })
            if 'min' in limits:
                constraints.append({
                    'type': 'ineq',
                    'fun': lambda x, idx=sector_indices: np.sum(x[idx]) - limits['min']
                })

    # Min/max holdings constraints
    # (More complex - requires binary variables for integer programming)
    # For now, use post-processing to filter small weights

    # Run optimization with constraints
    result_max_sharpe = sco.minimize(
        neg_sharpe_ratio,
        num_assets * [1./num_assets],
        args=args,
        method='SLSQP',
        bounds=bounds,
        constraints=constraints
    )

    # ... rest of optimization
```

#### Generate LLM Constraint Suggestions

```python
async def _generate_constraint_suggestions(
    self,
    optimal_weights: Dict[str, float],
    metrics: Dict[str, Any],
    scenarios: List[ScenarioForecast]
) -> List[str]:
    """
    Ask LLM to suggest constraints if optimization has issues.
    """
    # Check for issues
    issues = []

    # Concentration check
    max_weight = max(optimal_weights.values())
    if max_weight > 0.30:
        issues.append(f"Highest concentration: {max_weight:.1%}")

    # Low diversification
    if len(optimal_weights) < 5:
        issues.append(f"Only {len(optimal_weights)} holdings")

    # If issues found, ask LLM for suggestions
    if issues and self.llm_service:
        prompt = f"""
        The portfolio optimization has the following issues:
        {', '.join(issues)}

        Current allocation:
        {json.dumps(optimal_weights, indent=2)}

        Suggest 2-3 constraints to improve this portfolio.
        For each constraint, provide:
        - Type (asset/sector/diversification)
        - Specific values (max weight, min holdings, etc.)
        - Rationale

        Return as JSON with key "constraint_suggestions".
        """

        response = await self.llm_service.generate_json(prompt)
        return response.get("constraint_suggestions", [])

    return []
```

### Phase 2: Frontend UI

#### New Component: `ConstraintsPanel.tsx`

```tsx
interface ConstraintsPanelProps {
    constraints: PortfolioConstraints;
    onUpdate: (constraints: PortfolioConstraints) => void;
    onReoptimize: () => void;
    llmSuggestions: string[];
}

// Features:
// - Sliders for max position size
// - Sector constraint inputs
// - Excluded assets tag list
// - Apply LLM suggestions button
// - Re-optimize button
```

#### Update `PlanDetail.tsx`

Add "Constraints" tab next to Overview/Accounts/Settings.

---

## Example User Journey

### Step 1: Initial Optimization
```
User: Optimize $100K with moderate risk
System: Returns allocation with 40% Gold
```

### Step 2: AI Review
```
LLM Report: "Gold allocation of 40% may be too high for
moderate risk profile. Consider limiting to 10-15%."

[Suggest Constraint: Max Gold 10%]
```

### Step 3: User Adjusts
```
User: Clicks "Apply" on constraint
User: Also sets "Max Position: 20%"
User: Clicks "Re-optimize"
```

### Step 4: Constrained Result
```
New Allocation:
SPY: 30%
VEA: 20%
VWO: 15%
GLD: 10%  ← Now within constraint
BND: 15%
VNQ: 10%

✅ Better diversified, still efficient frontier
```

---

## Sector Mapping (Config)

### Backend Config Structure

```yaml
# config.yaml
etf_universe:
  SPY:
    name: "SPDR S&P 500 ETF Trust"
    sector: "US Equity"
    asset_class: "Equity"
    expense_ratio: 0.0945

  GLD:
    name: "SPDR Gold Shares"
    sector: "Commodities"
    asset_class: "Commodity"
    expense_ratio: 0.40

  BND:
    name: "Vanguard Total Bond Market ETF"
    sector: "Bonds"
    asset_class: "Fixed Income"
    expense_ratio: 0.035

# ... more ETFs

sector_list:
  - US Equity
  - International Equity
  - Bonds
  - Commodities
  - Real Estate
  - Emerging Markets
```

---

## API Changes

### Update `OptimizationRequest`

```python
class OptimizationRequest(BaseModel):
    amount: float
    currency: str
    risk_tolerance: Optional[float] = None
    excluded_tickers: Optional[List[str]] = []

    # NEW: Constraints
    constraints: Optional[PortfolioConstraints] = None
```

### New Endpoint

```python
@router.post("/portfolio/optimize/{job_id}/constrain")
async def add_constraints_and_reoptimize(
    job_id: str,
    constraints: PortfolioConstraints,
    optimizer_service: PortfolioOptimizerService = Depends(get_portfolio_optimizer_service)
):
    """Re-optimize with new constraints"""
    result = await optimizer_service.reoptimize_with_constraints(
        job_id, constraints
    )
    return result
```

---

## Testing Scenarios

### Test 1: Concentration Limit
```python
# Without constraint: SPY 50%, GLD 40%, BND 10%
# With max_position=0.30: SPY 30%, VEA 25%, GLD 25%, BND 20%
```

### Test 2: Sector Cap
```python
# Without constraint: Tech 60% (too concentrated)
# With sector_cap={"Technology": 0.30}: Tech 30%, spread to other sectors
```

### Test 3: Exclude Assets
```python
# User wants ESG portfolio
# excluded_assets = ["XOM", "CVX"] (oil companies)
# Optimization avoids these
```

---

## Future Enhancements

1. **Cardinality Constraints**: Require exact number of holdings (integer programming)
2. **Turnover Constraints**: Limit trades from previous portfolio
3. **Factor Constraints**: Limit exposure to factors (value, size, momentum)
4. **Dynamic Constraints**: Adjust based on market conditions
5. **Learning**: System learns user preferences over time

---

## References

- Portfolio Optimization with Constraints: https://plotly.com/python/v3/ipython-notebooks/markowitz-portfolio-optimization/
- SciPy optimization with constraints: https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html
- Sector ETF list: https://www.ssga.com/us/en/intermediaries/etfs/spdr-sector-etfs
