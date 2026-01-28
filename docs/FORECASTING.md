# Forecasting Methodology

## Overview

This document explains the theoretical and quantitative foundations of our forecasting system from a financial engineering perspective. The system employs a **hybrid multi-stage approach** that combines classical stochastic models, machine learning, and AI-driven scenario analysis to generate robust financial forecasts.

## Theoretical Framework

### The Challenge of Financial Forecasting

Financial markets exhibit complex dynamics that make single-model forecasting approaches unreliable:

- **Non-stationarity**: Market regimes shift (bull → bear → sideways)
- **Fat tails**: Extreme events occur more frequently than Gaussian distributions predict
- **Volatility clustering**: Periods of high volatility follow each other
- **Mean reversion**: Some asset classes (bonds, commodities) revert to long-term means
- **Jump risk**: Prices can discontinuously gap due to news/events
- **Multifactor dependence**: Assets react to macro, technical, sentiment, and fundamental factors

No single model captures all these phenomena. Our solution: **ensemble forecasting with regime-aware scenario analysis**.

## Stage 1: Baseline Stochastic Models

### Geometric Brownian Motion (GBM)

**Theoretical Foundation:**

GBM models asset prices as a continuous-time stochastic process following the stochastic differential equation:

```
dS_t = μS_t dt + σS_t dW_t
```

Where:
- `S_t` = Asset price at time t
- `μ` = Drift (expected return)
- `σ` = Volatility (standard deviation of returns)
- `W_t` = Wiener process (Brownian motion)
- `dW_t ~ N(0, √dt)` = Random shock

**Discrete-time solution for simulation:**

```
S_{t+Δt} = S_t × exp[(μ - ½σ²)Δt + σ√Δt × Z]
```

Where `Z ~ N(0,1)` is a standard normal random variable.

**Properties:**
- Log-normally distributed prices (ensures prices stay positive)
- Constant drift and volatility (limitation: doesn't capture regime changes)
- Closed-form solution for option pricing (Black-Scholes)
- Good baseline for equities during stable periods

**Enhancements in our implementation:**
- Multi-horizon analysis (1mo, 3mo, 6mo, 1yr)
- Scenario-based drift/volatility adjustments
- Confidence intervals at multiple percentiles (5th, 25th, 50th, 75th, 95th)
- Parallel Monte Carlo (1000+ paths for statistical significance)

### ARIMA (AutoRegressive Integrated Moving Average)

**Theoretical Foundation:**

ARIMA captures time-series dependencies and trends:

```
ARIMA(p, d, q): (1 - φ₁L - ... - φₚLᵖ)(1 - L)ᵈ Y_t = (1 + θ₁L + ... + θ_qLᵠ)ε_t
```

Where:
- `p` = AutoRegressive order (past values influence current)
- `d` = Differencing order (achieve stationarity)
- `q` = Moving Average order (past errors influence current)
- `L` = Lag operator
- `ε_t ~ N(0, σ²)` = White noise

**Stationarity requirement:**
ARIMA requires constant mean and variance. We test stationarity using the **Augmented Dickey-Fuller test**:
- H₀: Unit root exists (non-stationary)
- H₁: Stationary
- If p-value < 0.05: Reject H₀ → series is stationary

**Model selection:**
We minimize **AIC (Akaike Information Criterion)**:

```
AIC = 2k - 2ln(L̂)
```

Where `k` = number of parameters, `L̂` = maximized likelihood function. Lower AIC = better trade-off between fit and complexity.

**Strengths:**
- Captures autocorrelation and momentum
- Good for short-term trend detection
- Handles mean-reverting series well
- Provides confidence intervals via Kalman filter

**Limitations:**
- Assumes linear relationships
- Max 60-day horizon (becomes unreliable beyond)
- Struggles with structural breaks/regime changes

### Ensemble Combination

We combine GBM and ARIMA outputs using **weighted ensembles**:

```
Forecast_ensemble = w₁ × Forecast_GBM + w₂ × Forecast_ARIMA
```

Weights are asset-class dependent:
- Equities: 70% GBM, 30% ARIMA (momentum dominates)
- Fixed Income: 60% ARIMA, 40% GBM (mean reversion dominates)
- Commodities: 80% GBM, 20% ARIMA (high volatility)

## Stage 2: Market Regime Detection

### Why Regime Detection Matters

Markets operate in distinct **regimes** with different statistical properties:

| Regime | Drift | Volatility | Correlation | Best Model |
|--------|-------|------------|-------------|------------|
| Bull (strong uptrend) | High | Low | Moderate | GBM with trend boost |
| Bear (downtrend) | Negative | High | High (crashes correlate) | GBM with volatility premium |
| Sideways (range-bound) | Near zero | Low | Low | Mean-reverting models |
| Transition | Uncertain | Spiking | Shifting | Scenario analysis |

### Technical Indicators for Regime Classification

**Trend Strength:**
- **ADX (Average Directional Index)**: Measures trend strength regardless of direction
  - ADX > 50: Strong trend
  - ADX 25-50: Trending
  - ADX < 20: Ranging

- **SMA Crossovers**: Price relative to moving averages indicates trend
  - Price > SMA(50) > SMA(200): Uptrend
  - Price < SMA(50) < SMA(200): Downtrend

**Momentum:**
- **RSI (Relative Strength Index)**: Overbought/oversold conditions
  - RSI > 70: Overbought (potential reversal)
  - RSI < 30: Oversold (potential reversal)
  - RSI > 50: Bullish momentum

- **MACD**: Trend momentum and changes
  - MACD > Signal: Bullish
  - Histogram expansion: Momentum strengthening

**Volatility:**
- **Bollinger Bandwidth**: `(Upper - Lower) / Middle`
  - Bandwidth > 5%: High volatility regime
  - Bandwidth < 3%: Low volatility regime

- **ATR (Average True Range)**: Absolute volatility measure
  - High ATR: Intraday volatility elevated

### Market Regime Classification

Our system classifies markets into:

```
Regime = {
  trend_direction: "uptrend" | "downtrend" | "sideways",
  trend_strength: "strong" | "moderate" | "weak",
  volatility_regime: "high" | "normal" | "low",
  sentiment: "very_bullish" | "bullish" | "neutral" | "bearish" | "very_bearish"
}
```

This classification drives **parameter adjustments** in Stage 3.

## Stage 3: Scenario-Based Refinement

### The Scenario Approach

Instead of point forecasts, we generate **scenario-based forecasts** that account for regime uncertainty:

```
Scenarios = {
  Base Case (60% weight):    Current regime continues
  Bull Case (20% weight):    Favorable outcome, reduced volatility
  Bear Case (20% weight):    Adverse outcome, elevated volatility
}
```

### Scenario Parameter Adjustments

Each scenario adjusts drift and volatility:

**Base Case:**
```
drift_adj = trend_adjustment  (±2% based on technicals)
vol_adj   = 0
```

**Bull Case:**
```
drift_adj = +5%  (optimistic drift)
vol_adj   = -10% (volatility compression)
```

**Bear Case:**
```
drift_adj = -5%  (pessimistic drift)
vol_adj   = +20% (volatility expansion)
```

### AI-Enhanced Scenario Generation

When available, we use an **LLM (Large Language Model)** to synthesize multiple information sources:

**Inputs to LLM:**
1. Baseline forecast results (GBM + ARIMA)
2. Technical indicator analysis
3. Macro economic regime (expansion/recession, inflation, monetary policy)
4. Recent news sentiment (if available)

**LLM Task:**
```
"Given the above analysis, generate 3 scenarios (Base, Bull, Bear) with:
- Probability weights (must sum to 1.0)
- Drift adjustments (justified by technicals/macro)
- Volatility adjustments (justified by regime)
- Narrative explanation"
```

**Output:**
The LLM provides nuanced adjustments that a rule-based system might miss, such as:
- "Yield curve inversion suggests recession risk → increase bear case weight to 30%"
- "Fed pivot expected → volatility may compress despite uncertainty"
- "Earnings season approaching → increase vol_adj temporarily"

This **hybrid approach** (quantitative models + AI interpretation) captures both statistical regularities and contextual nuance.

## Stage 4: Risk Metrics

### Value at Risk (VaR)

**Definition:** Maximum expected loss at a given confidence level over a period.

**Historical VaR:**
```
VaR_α = quantile(returns, 1 - α)
```

Where `α = 0.95` or `0.99`. For 95% VaR:
- "There is a 5% chance of losing at least VaR_95"
- Interpretation: "In 1 out of 20 days, we expect to lose ≥ VaR_95"

**Parametric VaR (assuming normality):**
```
VaR_α = μ - σ × z_α
```

Where `z_α` is the standard normal critical value (z₀.₀₅ = -1.645).

**Limitations:**
- VaR doesn't tell you **how much** you could lose beyond the threshold
- Assumes normal distribution (underestimates tail risk)
- Doesn't capture "black swan" events

### Conditional VaR (CVaR / Expected Shortfall)

**Definition:** Average loss **given** that we've exceeded the VaR threshold.

```
CVaR_α = E[Return | Return ≤ VaR_α]
```

**Interpretation:**
- "On days when we lose more than VaR, the average loss is CVaR"
- CVaR ≥ VaR always (provides worst-case expectation)
- **Coherent risk measure** (satisfies subadditivity: VaR doesn't)

**Importance:**
CVaR is required for regulatory capital calculations (Basel Accords) because it captures tail risk better than VaR.

### Maximum Drawdown

**Definition:** Peak-to-trough decline during a specific period.

```
Drawdown_t = (Price_t - max(Price_0...Price_t)) / max(Price_0...Price_t)
Max Drawdown = min(Drawdown)
```

**Interpretation:**
- "Worst-case loss from peak to trough"
- Measures recovery time (how long to get back to water)
- Critical for risk management and position sizing

**Psychological impact:**
Drawdowns of >20% trigger panic selling; >50% trigger capitulation. Our system flags high-drawdown risk to warn users.

### Sharpe Ratio

**Definition:** Risk-adjusted return (return per unit of risk).

```
Sharpe = (E[R] - R_f) / σ(R)
```

Where:
- `E[R]` = Expected return
- `R_f` = Risk-free rate (e.g., 4% Treasury yield)
- `σ(R)` = Volatility of returns

**Interpretation:**
- Sharpe > 1: Good risk-adjusted return
- Sharpe > 2: Excellent
- Sharpe < 1: Returns don't compensate for risk

**Critique:**
Sharpe penalizes **upside volatility** equally with downside. A stock that gaps up 10% has higher σ → lower Sharpe (misleading).

### Sortino Ratio

**Definition:** Downside-risk-adjusted return (only penalizes bad volatility).

```
Sortino = (E[R] - R_f) / σ_downside(R)
```

Where `σ_downside` only uses returns < target (usually 0 or R_f).

**Advantage:**
Distinguishes between "good volatility" (upside jumps) and "bad volatility" (downside crashes).

## Macro Economic Integration

### Why Macro Matters in Forecasting

Asset prices don't move in isolation. They respond to:

1. **Business Cycle**: GDP growth, corporate earnings
2. **Monetary Policy**: Interest rates, QE/tightening
3. **Inflation**: Erodes real returns, affects discount rates
4. **Risk Sentiment**: "Risk-on" vs "Risk-off" regimes

### Key Macro Indicators (US)

**Growth:**
- **GDP Growth**: Economic expansion speed
  - >3%: Strong expansion (bullish for equities)
  - 0-2%: Slow growth (cautious)
  - <0%: Recession (bearish)

- **Unemployment**: Labor market health
  - <4%: Tight labor market (wage inflation risk)
  - >6%: Labor market weakness (recession risk)

**Inflation:**
- **CPI / PCE**: Consumer price changes
  - >4%: High inflation (Fed tightening risk)
  - 2-3%: Target range (optimal)
  - <1%: Deflation risk (Fed easing)

**Monetary Policy:**
- **Fed Funds Rate**: Cost of borrowing
  - Hiking cycle: Bearish for growth stocks
  - Cutting cycle: Bullish for equities

- **Yield Curve**: 10y - 2y Treasury spread
  - Inversion (10y < 2y): Recession signal
  - Steepening: Growth expectations

**Risk Sentiment:**
- **Dollar Index (DXY)**: USD strength
  - Strong DXY: Risk-off (flight to safety)
  - Weak DXY: Risk-on (carry trades)

### Macro Regime Classification

```
Economic Regime = {
  growth_phase: "expansion" | "recovery" | "slowdown" | "recession",
  inflation_regime: "high" | "target" | "low",
  monetary_policy: "tightening" | "neutral" | "easing"
}
```

**Example:**
```
"Growth: expansion (3.2% GDP), Inflation: elevated (4.1% CPI),
 Policy: tightening (Fed funds 5.25%)"

→ Implications: Soft-landing risk, high volatility regime,
   overweight quality, reduce duration
```

## Risk-On / Risk-Off Assessment

### Concept

Markets alternate between **risk-on** (appetite for risky assets) and **risk-off** (flight to safety):

| Regime | Equities | Bonds | USD | Volatility |
|--------|----------|-------|-----|------------|
| **Risk-On** | ↑ | ↓ (rates rise) | ↓ | ↓ |
| **Risk-Off** | ↓ | ↑ (flight to safety) | ↑ | ↑ |

### Indicators

**Current Implementation:**
- VIX (volatility index)
- Technicals (trend strength)
- Macro (monetary policy stance)

**Future Enhancements:**
- Put/Call ratio: Extreme readings signal reversals
- Advance/Decline line: Breadth of market participation
- High/Low index: New highs vs new lows
- Margin debt: Leverage in the system

## Future Model Enhancements

### Jump Diffusion Model

**Motivation:** GBM assumes continuous paths, but markets **gap** (earnings surprises, geopolitical events, Fed announcements).

**Model:**
```
dS_t = μS_t dt + σS_t dW_t + J_t S_t dN_t
```

Where:
- `J_t` = Jump size (log-normal distribution)
- `dN_t ~ Poisson(λ)` = Jump arrival (rare events)
- `λ` = Jump intensity (expected jumps per year)

**Use case:** Tech stocks, biotech, earnings season, crypto.

### Mean-Reverting Models (Ornstein-Uhlenbeck)

**Motivation:** Some asset classes revert to long-term means (commodities, bonds, currencies, volatility).

**Model:**
```
dX_t = θ(μ - X_t)dt + σdW_t
```

Where:
- `X_t` = Deviation from mean
- `θ` = Speed of mean reversion
- `μ` = Long-term mean
- `σ` = Volatility

**Use case:** Fixed income, commodities, FX, VIX futures.

### Regime-Switching Models

**Motivation:** Markets have distinct "states" with different parameters.

**Model (Hamilton, 1989):**
```
S_t = {
  μ₁ + σ₁W_t  (probability p₁)  # Bull regime
  μ₂ + σ₂W_t  (probability p₂)  # Bear regime
}
```

**Transition probability matrix:**
```
P = [ p₁₁  p₁₂ ]
    [ p₂₁  p₂₂ ]
```

Where `pᵢⱼ` = P(Regime_j | Regime_i)

**Use case:** Capturing structural breaks, business cycle modeling.

### Prophet (Facebook)

**Motivation:** Captures **seasonality** and **holidays** that ARIMA misses.

**Model:**
```
y(t) = g(t) + s(t) + h(t) + ε_t
```
- `g(t)` = Trend (piecewise linear / logistic)
- `s(t)` = Seasonality (Fourier series)
- `h(t)` = Holiday effects
- `ε_t` = Error term

**Use case:** Retail stocks (seasonal sales), commodities (weather patterns), equity indices.

### LSTM (Long Short-Term Memory)

**Motivation:** Deep learning for **nonlinear pattern recognition**.

**Architecture:**
- Input: Window of past prices + technical indicators + macro variables
- Hidden layers: LSTM cells (memory + forget gates)
- Output: Future price distribution

**Advantages:**
- Captures complex nonlinearities
- Learns from multiple features simultaneously
- Adapts to changing market conditions

**Challenges:**
- Requires massive data (10k+ observations)
- Black box (hard to interpret)
- Overfitting risk
- Computationally expensive

**Use case:** Intraday forecasting, high-frequency trading, alternative data integration.

## Future Data Sources

### Market Internals

**Put/Call Ratio:**
```
PCR = Total Put Volume / Total Call Volume
```
- PCR > 1: Excessive bearishness (contrarian buy signal)
- PCR < 0.5: Excessive bullishness (contrarian sell signal)

**Advance/Decline Line:**
```
ADL = cumulative(Advancing Stocks - Declining Stocks)
```
- ADL rising while market flat: Breadth strengthening (bullish)
- ADL falling while market flat: Breadth weakening (bearish)

**New Highs / New Lows:**
```
HL Ratio = Stocks at 52-week Highs / Stocks at 52-week Lows
```
- HH > HL: Healthy uptrend
- LH dominating: Distribution phase

**VIX (CBOE Volatility Index):**
- Implied volatility from S&P 500 options
- VIX > 30: Fear regime (buy when there's blood in the streets)
- VIX < 12: Complacency (reduce risk)

**Use Cases:**
- Market timing (entry/exit signals)
- Regime detection (risk-on vs risk-off)
- Sentiment extremes (contrarian indicators)

### Sentiment Analysis

**News Sentiment:**
- LLM-scored news articles (positive/negative/neutral)
- Sentiment momentum (trending more positive/negative)

**Social Media:**
- Twitter/X sentiment (retweets, mentions)
- Reddit sentiment (r/wallstreetbets mentions)
- News vs. hype divergence

**Analyst Ratings:**
- Buy/sell/hold recommendations
- Price target changes
- Consensus vs. reality

**Use Cases:**
- Short-term reversals (sentiment extremes)
- Earnings anticipation
- Narrative-driven moves (meme stocks)

## Integration Framework

### Multi-Model Ensemble

Future architecture will weight models based on:

1. **Historical accuracy** (backtesting performance)
2. **Regime appropriateness** (some models work better in certain regimes)
3. **Confidence scoring** (LLM assesses model fit)

```
Weight_t = f(Accuracy_t-1, Regime_t, Confidence_t)
Forecast_ensemble = Σ Weight_i × Forecast_i
```

### Adaptive Learning

The system will **track which models work best** in which conditions:

```
Model Performance Database:
- GBM: Best in low-vol trending markets
- ARIMA: Best in mean-reverting regimes
- Jump Diffusion: Best around earnings/events
- Prophet: Best with seasonal assets
- LSTM: Best with high-frequency data
```

Over time, the system learns to **auto-select** the best model for the current regime.

## Theoretical Limitations

### Efficient Market Hypothesis (EMH)

**Strong Form:** All information (public + private) is reflected in prices → **No alpha possible**

**Semi-Strong:** All public information is reflected → **Fundamental analysis doesn't work**

**Weak Form:** Past price data is reflected → **Technical analysis doesn't work**

**Our Position:** Markets are **not perfectly efficient** due to:
- Behavioral biases (fear, greed, herding)
- Information asymmetry (insiders, professional analysts)
- Frictions (transaction costs, taxes)
- Adaptive markets (loopholes appear and disappear)

Therefore, **skilled forecasting can add value**, but:
- Edge is small and ephemeral
- Risk management is critical
- Continuous adaptation is necessary

### Black Swans (Taleb, 2007)

**Definition:** Rare, high-impact events that are **not predictable** using historical data.

Examples:
- 1987 Black Monday
- 2008 Financial Crisis
- 2020 COVID Crash
- 2022 Russia-Ukraine War

**Our approach:**
- Acknowledge we cannot predict black swans
- Use **stress testing** (bear case scenarios)
- Emphasize **risk management** (VaR, CVaR, drawdown limits)
- Maintain humility in confidence intervals

## Conclusion

Our forecasting system combines:

1. **Proven quantitative models** (GBM, ARIMA) with solid theoretical foundations
2. **Regime-aware adjustments** based on technical and macro analysis
3. **AI-enhanced scenario generation** for contextual nuance
4. **Comprehensive risk metrics** (VaR, CVaR, drawdown, Sharpe/Sortino)
5. **Extensible architecture** for adding new models and data sources

**No system is perfect**, but by combining multiple approaches, acknowledging uncertainty, and managing risk rigorously, we aim to provide **probabilistic forecasts** that inform decision-making without promising impossible precision.

### Key Principles

- **Probabilistic, not deterministic**: We forecast distributions, not point estimates
- **Scenario-based, not single-path**: We prepare for multiple outcomes
- **Regime-aware, not static**: We adapt to changing market conditions
- **Risk-first, not return-maximizing**: We prioritize capital preservation
- **Humility, not hubris**: We acknowledge limitations and model uncertainty

### References

- Hull, J. (2022). *Options, Futures, and Other Derivatives* (11th ed.)
- Tsay, R. S. (2010). *Analysis of Financial Time Series* (3rd ed.)
- Hamilton, J. D. (1989). "A New Approach to the Economic Analysis of Nonstationary Time Series and the Business Cycle." *Econometrica*
- Taleb, N. N. (2007). *The Black Swan: The Impact of the Highly Improbable*
- Cont, R. (2001). "Empirical properties of asset returns: stylized facts and statistical issues." *Quantitative Finance*
