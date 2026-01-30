# Portfolio Optimization Methodology

## Overview

This document explains the theoretical and quantitative foundations of our portfolio optimization system from a financial engineering perspective. The system implements **Modern Portfolio Theory (MPT)** with advanced enhancements including transaction cost modeling, constraint satisfaction, and multi-objective optimization to construct optimal portfolios.

## Theoretical Framework

### The Portfolio Problem

**Given:** A set of n assets with expected returns {R₁, R₂, ..., Rₙ} and covariance matrix Σ

**Find:** Optimal weights {w₁, w₂, ..., wₙ} that maximize risk-adjusted returns

**Constraints:**
- Full investment: Σwᵢ = 1 (all capital allocated)
- No short selling: wᵢ ≥ 0 (long-only positions)
- Position limits: wᵢ ≤ w_max (diversification requirement)
- Sector/exposure constraints (optional)

### Why Mean-Variance Optimization?

**Harry Markowitz (1952)** revolutionized finance by showing that investors should care about **portfolio returns and risk**, not individual asset characteristics.

**Key Insight:** By combining assets with low correlations, we can reduce portfolio volatility without sacrificing returns.

**Mathematical Foundation:**
```
Portfolio Return: E[R_p] = Σ wᵢ × E[Rᵢ]
Portfolio Variance: σ²_p = wᵀΣw = Σᵢ Σⱼ wᵢwⱼσᵢⱼ
```

Where:
- `wᵢ` = Weight of asset i
- `E[Rᵢ]` = Expected return of asset i
- `σᵢⱼ` = Covariance between assets i and j
- `Σ` = Covariance matrix (n×n)

## Modern Portfolio Theory (MPT)

### Efficient Frontier

**Definition:** The set of portfolios that offer the **highest expected return** for a given level of risk, or the **lowest risk** for a given expected return.

**Mathematical Formulation:**

For a target return μₜ, find weights that minimize variance:

```
min  wᵀΣw
s.t. Σwᵢ = 1     (full investment)
     ΣwᵢRᵢ = μₜ   (target return)
     wᵢ ≥ 0       (no short selling)
```

**Properties:**
- Concave curve in risk-return space
- Northwest boundary of the feasible set
- Only portfolios **on the frontier** are rational
- Portfolios **below the frontier** are inefficient (dominated)

### The Optimal Portfolio

Among all efficient frontier portfolios, which one should an investor choose?

**Solution:** Maximize the **Sharpe Ratio** (risk-adjusted return)

```
Sharpe Ratio = (E[R_p] - R_f) / σ_p
```

Where:
- `E[R_p]` = Portfolio expected return
- `R_f` = Risk-free rate (e.g., 4% Treasury yield)
- `σ_p` = Portfolio volatility (standard deviation)

**Optimal Portfolio = Maximum Sharpe Ratio Portfolio**

This is the **tangency portfolio** when combined with the risk-free asset, forming the **Capital Market Line (CML)**.

## Risk and Return Estimation

### Expected Returns

**Challenge:** Expected returns are **unobservable** and notoriously difficult to estimate.

**Our Approach:** We use a **hybrid forecasting system** combining:

1. **Historical Returns** (baseline)
   ```
   R̄ᵢ = (1/T) Σ Rᵢ,t
   ```
   Limitation: Past performance ≠ future results

2. **Forecasted Returns** (forward-looking)
   - Geometric Brownian Motion (GBM) simulations
   - ARIMA time-series models
   - Ensemble forecasts with regime adjustments
   - See: `docs/FORECASTING.md`

3. **Dividend Yields** (income component)
   ```
   Total Return = Price Return + Dividend Yield
   ```

4. **Expense Ratio Adjustment** (cost of custody)
   ```
   Net Return = Gross Return - Expense Ratio
   ```
   See: `docs/PORTFOLIO_FORECASTING_INTEGRATION.md`

**Final Expected Return:**
```
E[Rᵢ] = Forecast_Return + Dividend_Yield - Expense_Ratio
```

### Covariance Matrix Estimation

**Challenge:** Covariance matrices are:
- Noisy (especially with few observations)
- Non-stationary (correlations change over time)
- Dimensionality problem: n(n-1)/2 parameters to estimate

**Standard Approach:**
```
Σ = Cov(R) = (1/T) × (R - R̄)ᵀ(R - R̄)
```

**Sample Size Requirements:**
- For n assets, need T >> n observations
- Rule of thumb: T ≥ 10×n for stable estimates
- Our implementation: Use 1 year of daily data (T=252, n=10) ✓

**Covariance Shrinkage (Future Enhancement):**

When T is small relative to n, sample covariance is unstable. **Ledoit-Wolf shrinkage** stabilizes estimates:

```
Σ_shrink = δ × F + (1-δ) × S
```

Where:
- `S` = Sample covariance matrix
- `F` = Structured estimator (constant correlation)
- `δ` = Shrinkage intensity (0 to 1)

**Correlation vs Covariance:**
```
σᵢⱼ = ρᵢⱼ × σᵢ × σⱼ
```
- Correlation (ρᵢⱼ) is dimensionless, ranges [-1, 1]
- Covariance (σᵢⱼ) has units (returns squared)

**Key Correlations in Our Portfolio:**
- US Equities (SPY, QQQ, IWM): ρ ≈ 0.85-0.95 (highly correlated)
- Japan Equities (1306.T, 1321.T): ρ ≈ 0.90-0.95
- US-Japan Equities: ρ ≈ 0.30-0.50 (moderate)
- Bonds vs Equities: ρ ≈ -0.10 to 0.20 (low/negative)
- Commodities vs Equities: ρ ≈ -0.10 to 0.30 (low)

**Diversification Benefit:**
Low correlation assets reduce portfolio volatility:
```
σ²_portfolio = w₁²σ₁² + w₂²σ₂² + 2w₁w₂σ₁σ₂ρ
```
If ρ < 1, σ²_portfolio < (w₁σ₁ + w₂σ₂)²

## Optimization Algorithm

### Mathematical Formulation

**Objective:** Maximize Sharpe Ratio

```
max  (wᵀμ - R_f) / √(wᵀΣw)
```

**Equivalent formulation (convex optimization):**

```
max  wᵀμ - γ × wᵀΣw
s.t. Σwᵢ = 1
     wᵢ ≥ 0  (no short selling)
     wᵢ ≤ w_max  (position limits, optional)
```

Where `γ` is the risk aversion parameter.

### Numerical Solution

**Algorithm:** Sequential Least Squares Programming (SLSQP)

**Why SLSQP?**
- Handles nonlinear objectives with linear constraints
- Efficient for medium-scale problems (n < 100)
- Guaranteed convergence for convex problems
- Implemented in `scipy.optimize.minimize`

**Implementation Steps:**

1. **Define objective function:**
   ```python
   def neg_sharpe_ratio(weights, expected_returns, cov_matrix):
       portfolio_return = np.dot(weights, expected_returns)
       portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
       sharpe_ratio = (portfolio_return - risk_free_rate) / np.sqrt(portfolio_variance)
       return -sharpe_ratio  # Minimize negative Sharpe = Maximize Sharpe
   ```

2. **Define constraints:**
   ```python
   constraints = {
       'type': 'eq',
       'fun': lambda w: np.sum(w) - 1  # Weights sum to 1
   }
   ```

3. **Define bounds:**
   ```python
   bounds = tuple((0.0, 1.0) for asset in range(n_assets))  # Long-only
   ```

4. **Initial guess:**
   ```python
   initial_weights = np.array([1/n_assets] * n_assets)  # Equal weight
   ```

5. **Optimize:**
   ```python
   result = sco.minimize(
       neg_sharpe_ratio,
       initial_weights,
       args=(expected_returns, cov_matrix),
       method='SLSQP',
       bounds=bounds,
       constraints=constraints
   )
   ```

### Efficient Frontier Generation

To visualize the frontier, we solve for a range of target returns:

```python
# Find minimum and maximum returns
min_vol_portfolio = minimize_volatility(expected_returns, cov_matrix)
max_return = max(expected_returns)  # 100% in highest-return asset

# Generate frontier points
target_returns = np.linspace(min_return, max_return, 20)
efficient_frontier = []

for target in target_returns:
    # Minimize variance subject to target return
    constraints = (
        {'type': 'eq', 'fun': lambda w: np.sum(w) - 1},
        {'type': 'eq', 'fun': lambda w: np.dot(w, expected_returns) - target}
    )
    result = sco.minimize(portfolio_volatility, initial_weights,
                          args=(expected_returns, cov_matrix),
                          method='SLSQP', bounds=bounds,
                          constraints=constraints)
    efficient_frontier.append(result)
```

## Transaction Costs and Constraints

### Commission Modeling

**Challenge:** Standard MVO assumes frictionless trading. Real portfolios incur transaction costs.

**Our Implementation:**

1. **Estimate number of trades:**
   ```python
   active_assets = {ticker: weight for ticker, weight in weights.items()
                    if weight > 0.001}  # >0.1% threshold
   num_trades = len(active_assets)
   ```

2. **Calculate commission:**
   ```python
   if commission_type == "flat_per_trade":
       total_commission = num_trades * commission_rate
   elif commission_type == "percentage":
       total_commission = investment_amount * commission_rate
   ```

3. **Reduce investable amount:**
   ```python
   net_investment = initial_amount - total_commission
   ```

4. **Allocate net investment:**
   ```python
   for ticker, weight in active_assets.items():
       amount = net_investment * weight
       shares = amount / last_price
   ```

**Future Enhancement:** Transaction cost models that explicitly penalize trading:

```
max  wᵀμ - γ×wᵀΣw - λ×TC(w - w₀)
```

Where:
- `TC()` = Transaction cost function (convex)
- `w₀` = Current portfolio weights
- `λ` = Cost penalty parameter

### Custody Fees (Expense Ratios)

**Challenge:** ETFs charge ongoing annual fees (expense ratios) that reduce returns.

**Our Implementation:**

1. **Load expense ratios from config:**
   ```python
   expense_ratios = {
       "SPY": 0.0009,  # 0.09% annually
       "QQQ": 0.0020,  # 0.20% annually
       "GLD": 0.0040,  # 0.40% annually
       ...
   }
   ```

2. **Adjust expected returns:**
   ```python
   for ticker in expected_returns.index:
       expected_returns[ticker] -= expense_ratios.get(ticker, 0.0)
   ```

3. **Calculate annual custody cost:**
   ```python
   annual_custody_cost = Σ (investment_amount × weight × expense_ratio)
   ```

**Impact on Optimization:**
- Higher-fee assets (commodities, some international ETFs) have lower net returns
- Optimizer naturally favors low-fee alternatives when risk-adjusted returns are similar
- Promotes cost-efficient portfolio construction

### Practical Constraints

**Minimum Position Size:**
- Trading in round lots (100 shares)
- Minimum dollar amount per position
- Our implementation: Filter weights < 0.1% (de minimis)

**Maximum Position Size:**
- Regulatory limits (e.g., 5% for UCITS funds)
- Diversification requirements
- Risk concentration limits
- Our implementation: Optional `max_weight` parameter

**Sector/Asset Class Limits:**
- Cap exposure to specific sectors (e.g., max 30% tech)
- Ensure diversification across asset classes
- Our implementation: Via `excluded_tickers` parameter

**Turnover Constraints:**
- Limit portfolio churn to reduce trading costs
- Typical max: 20-30% annual turnover
- Future enhancement

## Risk Metrics

### Portfolio Volatility

**Definition:** Standard deviation of portfolio returns

```
σ_p = √(wᵀΣw)
```

**Interpretation:**
- σ_p = 15%: "In 68% of years, returns will be within ±15% of the mean"
- σ_p = 20%: "High volatility portfolio"

**Annualization:**
```
σ_annual = σ_daily × √252
```

### Value at Risk (VaR)

**Definition:** Maximum expected loss at a confidence level α

```
VaR_α = μ_p - z_α × σ_p
```

Where `z_α` is the standard normal critical value:
- 95% VaR: z₀.₀₅ = 1.645
- 99% VaR: z₀.₀₁ = 2.326

**Interpretation:**
- "There is a 5% probability of losing at least VaR_95 in a year"

**Limitations:**
- Assumes normal distribution (underestimates tail risk)
- Doesn't show losses beyond the threshold
- Not a coherent risk measure

### Conditional VaR (CVaR / Expected Shortfall)

**Definition:** Average loss **given** that VaR is exceeded

```
CVaR_α = E[Loss | Loss ≥ VaR_α]
```

**Advantages:**
- Coherent risk measure (satisfies subadditivity)
- Captures tail risk
- Regulatory standard (Basel Accords)

### Maximum Drawdown

**Definition:** Peak-to-trough decline

```
Drawdown_t = (P_t - max(P_0...P_t)) / max(P_0...P_t)
Max Drawdown = min(Drawdown)
```

**Interpretation:**
- "Worst-case loss from peak to trough"
- Critical for risk management and psychological comfort

**Benchmark:** Max drawdown < 20% is considered acceptable for most investors.

### Sharpe Ratio

**Definition:** Risk-adjusted return

```
Sharpe = (E[R_p] - R_f) / σ_p
```

**Interpretation:**
- Sharpe > 2: Excellent risk-adjusted performance
- Sharpe > 1: Good performance
- Sharpe < 1: Returns don't compensate for risk

**Critique:**
- Penalizes upside and downside volatility equally
- Assumes returns are normally distributed
- Doesn't account for skewness or kurtosis

### Sortino Ratio (Future Enhancement)

**Definition:** Downside-risk-adjusted return

```
Sortino = (E[R_p] - R_f) / σ_downside
```

Where `σ_downside` only uses returns < target (usually R_f).

**Advantage:**
Distinguishes between "good volatility" (upside) and "bad volatility" (downside).

## Capital Asset Pricing Model (CAPM)

### Theoretical Foundation

**Assumptions:**
1. Investors are rational and risk-averse
2. Markets are efficient (no arbitrage)
3. Unlimited borrowing/lending at risk-free rate
4. Homogeneous expectations (everyone has same forecasts)
5. No taxes or transaction costs

**Key Result:** In equilibrium, all investors hold the **market portfolio** (tangency portfolio).

### Security Characteristic Line

**Expected return of asset i:**

```
E[R_i] = R_f + βᵢ × (E[R_m] - R_f)
```

Where:
- `βᵢ` = Cov(Rᵢ, R_m) / Var(R_m) = Systematic risk
- `E[R_m]` = Expected market return
- `E[R_m] - R_f` = Market risk premium

**Beta Interpretation:**
- β = 1: Asset moves with the market
- β > 1: High volatility (aggressive)
- β < 1: Low volatility (defensive)
- β < 0: Inverse relationship (rare)

### Alpha (Active Return)

**Definition:** Excess return over CAPM prediction

```
αᵢ = Rᵢ - [R_f + βᵢ × (R_m - R_f)]
```

**Interpretation:**
- α > 0: Outperformance (skill or luck)
- α < 0: Underperformance

**Our System:**
- Portfolio optimization aims to maximize **portfolio Sharpe ratio**, not individual asset alpha
- However, our forecasting engine implicitly seeks alpha by identifying mispriced assets

## Multi-Asset Class Considerations

### Global Portfolio Construction

**Rationale:** Different asset classes have different risk/return profiles and correlations

| Asset Class | Expected Return | Volatility | Correlation w/ Equities | Role |
|-------------|----------------|------------|------------------------|------|
| US Equities | 8-10% | 15-20% | 1.00 | Growth engine |
| Dev. Market Equities | 7-9% | 15-18% | 0.70-0.85 | Diversification |
| Emerging Markets | 10-12% | 25-30% | 0.60-0.75 | High growth, high risk |
| Government Bonds | 2-4% | 5-10% | -0.10 to 0.20 | Safety, income |
| Corporate Bonds | 4-6% | 8-12% | 0.30-0.50 | Income, moderate risk |
| REITs | 7-9% | 15-20% | 0.60-0.80 | Inflation hedge, income |
| Commodities | 3-5% | 20-30% | -0.10 to 0.30 | Inflation hedge, diversification |
| Gold | 3-6% | 15-20% | -0.10 to 0.20 | Crisis hedge |

### Currency Risk (International Assets)

**Challenge:** Investing in foreign assets introduces currency exposure

**Example:**
- Buy Japanese ETF (1306.T) in USD
- Return = Asset Return (¥) + Currency Return (USD/JPY)
- If ¥ depreciates 10% vs USD, lose 10% on currency even if asset is flat

**Hedging (Future Enhancement):**
- Currency forwards/futures to hedge FX risk
- Increases cost but reduces volatility
- Decision depends on: Hedging cost vs. volatility reduction

### Rebalancing Strategy

**Challenge:** Portfolio weights drift as asset prices change

**Example:**
- Target: 60% equities, 40% bonds
- After bull market: 75% equities, 25% bonds (higher risk than intended)

**Rebalancing Approaches:**

1. **Time-based:** Rebalance quarterly/annually
   - Simple, predictable
   - May trade too frequently or too infrequently

2. **Threshold-based:** Rebalance when weights drift by ±5%
   - Trades only when necessary
   - More efficient

3. **Optimal rebalancing:** Balance transaction costs vs. tracking error
   - Complex optimization
   - Future enhancement

**Our Implementation:**
- Initial optimization provides target weights
- User responsible for rebalancing (manual or automated)
- Future: Auto-rebalancing recommendations

## Black-Litterman Model (Future Enhancement)

### Motivation

**Problem with standard MVO:**
- Sensitive to expected return estimates
- Small changes → large portfolio shifts
- Garbage in, garbage out

**Black-Litterman Solution:**
- Start from **market equilibrium** (market cap weights)
- Incorporate **investor views** as adjustments
- Shrink towards equilibrium (robustness)

### Mathematical Formulation

**Step 1: Equilibrium returns (reverse optimization)**

```
Π = λΣw_market
```

Where:
- `Π` = Equilibrium excess returns
- `λ` = Risk aversion coefficient
- `w_market` = Market cap weights
- `Σ` = Covariance matrix

**Step 2: Incorporate investor views**

```
Views: P × μ = Q + ε
```

Where:
- `P` = Pick matrix (which assets views apply to)
- `Q` = View returns
- `ε` ~ N(0, Ω) = View uncertainty

**Step 3: Posterior distribution (Bayesian)**

```
μ_BL = [(τΣ)⁻¹ + PᵀΩ⁻¹P]⁻¹ × [(τΣ)⁻¹Π + PᵀΩ⁻¹Q]
```

Where `τ` = Scalar uncertainty parameter

**Advantages:**
- More stable portfolios
- Intuitive way to express views
- Handles uncertain views naturally
- Avoids corner solutions (100% in one asset)

## Robust Optimization (Future Enhancement)

### Distributional Uncertainty

**Problem:** We don't know true expected returns or covariance

**Solution:** Optimize for **worst-case** within confidence set

```
max  min  wᵀμ
     μ∈U   s.t. portfolio constraints
```

Where `U` is uncertainty set (e.g., confidence interval around estimates).

**Result:** More conservative portfolios that perform well across scenarios.

## Implementation Details

### Data Requirements

**Price History:**
- Minimum: 1 year daily data (252 observations)
- Preferred: 3-5 years for stable estimates
- Frequency: Daily (weekly/monthly for illiquid assets)

**Dividends:**
- Total return calculation requires dividend history
- Adjusted prices already incorporate dividends
- Our system: Fetch separate dividend data

**Corporate Actions:**
- Splits, mergers, spinoffs
- Handled by yfinance automatically

### Numerical Stability

**Covariance Matrix Conditioning:**
- Condition number = σ_max / σ_min
- If >> 1000, matrix is ill-conditioned
- Solution: Regularization (shrinkage, near-correlation matrix)

**Weight Precision:**
- Weights < 0.1% are rounded to zero
- Reduces number of positions (transaction cost savings)
- Improves interpretability

### Performance Optimization

**Computational Complexity:**
- Covariance calculation: O(n²T)
- Optimization: O(n³) per solve (matrix inversion)
- Efficient frontier: O(n³ × m) where m = number of points
- For n=10 assets: Negligible (<1 second)
- For n=1000 assets: Significant (~minutes)

**Our Implementation:**
- n=10 ETFs: Fast enough for real-time optimization
- No caching needed (could add for larger universes)

## Theoretical Limitations

### Estimation Error

**Expected Returns:**
- Hard to estimate (high uncertainty)
- 5-year historical returns have ~20% standard error
- Forecasting helps but doesn't eliminate uncertainty

**Covariance Matrix:**
- Correlations are unstable (change over time)
- Crisis periods: Correlations converge to 1 (contagion)
- Underestimates tail risk (assumes normality)

### Non-Normality

**Fat Tails:**
- Real returns have fatter tails than Gaussian
- Extreme events (3σ, 4σ) occur more often than expected
- VaR underestimates true risk

**Skewness:**
- Equity returns: Negative skew (crashes are sharper than rallies)
- Option strategies: Highly skewed

**Solution:** Use **Expected Shortfall (CVaR)** instead of VaR

### Model Risk

**Assumption Violations:**
- Returns aren't normal (have fat tails, skewness)
- Correlations aren't stable (regime switching)
- Markets aren't efficient (but are highly competitive)
- Taxes and transaction costs matter

**Mitigation:**
- Stress testing (bear case scenarios)
- Diversification across asset classes
- Conservative assumptions
- Regular monitoring and rebalancing

## Conclusion

Our portfolio optimization system implements **Modern Portfolio Theory** with practical enhancements:

1. **Hybrid return estimation** (historical + forecast + dividends - fees)
2. **Transaction cost modeling** (commissions, custody fees)
3. **Multi-scenario analysis** (efficient frontier generation)
4. **Comprehensive risk metrics** (volatility, VaR, CVaR, drawdown, Sharpe)
5. **Extensible architecture** (future: Black-Litterman, robust optimization)

**Key Principles:**

- **Diversification:** The only free lunch in finance
- **Risk management:** Capital preservation first, returns second
- **Cost efficiency:** Minimize fees and transaction costs
- **Robustness:** Acknowledge model uncertainty, use conservative assumptions
- **Transparency:** Show all assumptions, metrics, and trade-offs

**No optimization system is perfect**, but by combining solid theory with practical constraints and ongoing monitoring, we aim to construct portfolios that balance risk and return for long-term wealth accumulation.

### References

- Markowitz, H. (1952). "Portfolio Selection." *Journal of Finance*
- Sharpe, W. F. (1966). "Mutual Fund Performance." *Journal of Business*
- Black, F., & Litterman, R. (1992). "Global Portfolio Optimization." *Financial Analysts Journal*
- Ledoit, O., & Wolf, M. (2004). "A Well-Conditioned Estimator for Large-Dimensional Covariance Matrices." *Journal of Multivariate Analysis*
- Fabozzi, F. J., et al. (2007). *Robust Portfolio Optimization and Management*
- Meucci, A. (2005). *Risk and Asset Allocation*
