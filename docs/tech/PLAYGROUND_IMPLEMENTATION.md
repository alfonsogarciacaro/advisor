# Playground & Historical Analysis Implementation Plan

## Overview
Enable users to "play" with investment strategies through scenario testing, historical backtesting, and stress simulation.

**Merged approach combining:**
- Strategy templates (pre-built constraints for quick starts)
- Custom scenarios (user-defined variations)
- Historical replay with bias prevention
- Sector-specific strategies (requires adding sector ETFs)

---

## Phase 0: Add Sector ETFs to Configuration

### New ETFs to Add

```yaml
# US Sector ETFs (Select Sector SPDRs)
  - symbol: "XLY"
    name: "Consumer Discretionary Select Sector SPDR"
    description: "Companies in consumer discretionary: retail, autos, media"
    asset_class: "equity_sectors"
    sector: "consumer_discretionary"
    market: "US"
    expense_ratio: 0.0010

  - symbol: "XLP"
    name: "Consumer Staples Select Sector SPDR"
    description: "Defensive sector: food, beverage, household products"
    asset_class: "equity_sectors"
    sector: "consumer_staples"
    market: "US"
    expense_ratio: 0.0010

  - symbol: "XLE"
    name: "Energy Select Sector SPDR"
    description: "Energy companies: oil, gas, equipment"
    asset_class: "equity_sectors"
    sector: "energy"
    market: "US"
    expense_ratio: 0.0010

  - symbol: "XLF"
    name: "Financial Select Sector SPDR"
    description: "Banks, insurance, investment firms"
    asset_class: "equity_sectors"
    sector: "financials"
    market: "US"
    expense_ratio: 0.0010

  - symbol: "XLV"
    name: "Health Care Select Sector SPDR"
    description: "Pharmaceuticals, healthcare providers, biotech"
    asset_class: "equity_sectors"
    sector: "healthcare"
    market: "US"
    expense_ratio: 0.0010

  - symbol: "XLI"
    name: "Industrial Select Sector SPDR"
    description: "Manufacturing, construction, aerospace"
    asset_class: "equity_sectors"
    sector: "industrials"
    market: "US"
    expense_ratio: 0.0010

  - symbol: "XLK"
    name: "Technology Select Sector SPDR"
    description: "Software, hardware, IT services"
    asset_class: "equity_sectors"
    sector: "technology"
    market: "US"
    expense_ratio: 0.0010

  - symbol: "XLB"
    name: "Materials Select Sector SPDR"
    description: "Chemicals, mining, materials"
    asset_class: "equity_sectors"
    sector: "materials"
    market: "US"
    expense_ratio: 0.0010

  - symbol: "XLRE"
    name: "Real Estate Select Sector SPDR"
    description: "REITs and real estate services"
    asset_class: "equity_sectors"
    sector: "real_estate"
    market: "US"
    expense_ratio: 0.0010

  - symbol: "XLU"
    name: "Utilities Select Sector SPDR"
    description: "Electric, gas, water utilities"
    asset_class: "equity_sectors"
    sector: "utilities"
    market: "US"
    expense_ratio: 0.0010

  - symbol: "XLC"
    name: "Communication Services Select Sector SPDR"
    description: "Telecom, media, internet"
    asset_class: "equity_sectors"
    sector: "communication_services"
    market: "US"
    expense_ratio: 0.0010

# Japan Sector ETFs (if available)
  - symbol: "1588.T"
    name: "NEXT FUNDS IT Index ETF"
    description: "Japanese technology sector"
    asset_class: "equity_sectors"
    sector: "technology"
    market: "JP"
    expense_ratio: 0.0015
```

---

## Phase 1: Backend - Strategy Templates Service

### New File: `backend/app/services/strategies_service.py`

```python
from typing import List, Dict
from app.models.portfolio import PortfolioConstraints

class StrategyTemplate:
    """Pre-built investment strategy with constraints"""
    strategy_id: str
    name: str
    description: str
    risk_level: str  # conservative, moderate, aggressive
    constraints: PortfolioConstraints
    icon: str
    tags: List[str]

class StrategiesService:
    """Provides pre-built strategy templates"""
    
    STRATEGIES = {
        "conservative_income": StrategyTemplate(
            strategy_id="conservative_income",
            name="Conservative Income",
            description="Focus on stability and dividends with low volatility",
            risk_level="conservative",
            constraints=PortfolioConstraints(
                max_volatility=0.10,
                min_dividend_yield=0.02,
                max_single_asset_weight=0.30,
                preferred_assets=["AGG", "XLP", "XLU", "VNQ"]
            ),
            icon="shield",
            tags=["income", "low-risk", "retirement"]
        ),
        
        "balanced_diversifier": StrategyTemplate(
            strategy_id="balanced_diversifier",
            name="Balanced Diversifier",
            description="Classic 60/40 style portfolio with diversification",
            risk_level="moderate",
            constraints=PortfolioConstraints(
                min_equity_ratio=0.55,
                max_equity_ratio=0.65,
                max_single_asset_weight=0.40,
                min_diversification_score=0.7
            ),
            icon="balance-scale",
            tags=["balanced", "all-weather"]
        ),
        
        "aggressive_growth": StrategyTemplate(
            strategy_id="aggressive_growth",
            name="Aggressive Growth",
            description="Maximize long-term returns with high equity exposure",
            risk_level="aggressive",
            constraints=PortfolioConstraints(
                min_equity_ratio=0.80,
                max_single_asset_weight=0.50,
                preferred_assets=["SPY", "QQQ", "IWM"]
            ),
            icon="trending-up",
            tags=["growth", "high-risk", "long-term"]
        ),
        
        "tech_heavy": StrategyTemplate(
            strategy_id="tech_heavy",
            name="Technology Focus",
            description="Overweight technology sector for growth potential",
            risk_level="aggressive",
            constraints=PortfolioConstraints(
                min_sector_weight={"technology": 0.40},
                max_single_asset_weight=0.35,
                preferred_assets=["QQQ", "XLK"]
            ),
            icon="microchip",
            tags=["sector-bet", "technology", "growth"]
        ),
        
        "healthcare_focus": StrategyTemplate(
            strategy_id="healthcare_focus",
            name="Healthcare Focus",
            description="Defensive growth through healthcare sector",
            risk_level="moderate",
            constraints=PortfolioConstraints(
                min_sector_weight={"healthcare": 0.35},
                max_single_asset_weight=0.40,
                preferred_assets=["XLV", "XLP", "JNJ"]
            ),
            icon="heart-pulse",
            tags=["sector-bet", "healthcare", "defensive"]
        ),
        
        "dividend_aristocrats": StrategyTemplate(
            strategy_id="dividend_aristocrats",
            name="Dividend Aristocrats",
            description="Focus on consistent dividend payers",
            risk_level="moderate",
            constraints=PortfolioConstraints(
                min_dividend_yield=0.025,
                max_volatility=0.15,
                preferred_sectors=["consumer_staples", "utilities", "healthcare"]
            ),
            icon="coins",
            tags=["income", "dividends"]
        ),
        
        "recession_proof": StrategyTemplate(
            strategy_id="recession_proof",
            name="Recession-Proof",
            description="Defensive sectors and bonds for economic downturns",
            risk_level="conservative",
            constraints=PortfolioConstraints(
                max_volatility=0.12,
                min_fixed_income_ratio=0.40,
                preferred_sectors=["consumer_staples", "utilities", "healthcare"],
                preferred_assets=["XLP", "XLU", "XLV", "AGG"]
            ),
            icon="umbrella",
            tags=["defensive", "low-risk"]
        ),
        
        "inflation_hedge": StrategyTemplate(
            strategy_id="inflation_hedge",
            name="Inflation Hedge",
            description="Commodities and real estate to protect against inflation",
            risk_level="moderate",
            constraints=PortfolioConstraints(
                min_commodity_weight=0.15,
                min_real_estate_weight=0.15,
                preferred_assets=["GLD", "USO", "VNQ", "XLRE"]
            ),
            icon="fire",
            tags=["inflation", "commodities", "real-estate"]
        )
    }
    
    def get_all_strategies(self) -> List[StrategyTemplate]:
        """List all available strategies"""
        return list(self.STRATEGIES.values())
    
    def get_strategy(self, strategy_id: str) -> StrategyTemplate:
        """Get specific strategy by ID"""
        return self.STRATEGIES.get(strategy_id)
    
    def get_strategies_by_risk(self, risk_level: str) -> List[StrategyTemplate]:
        """Filter strategies by risk level"""
        return [s for s in self.STRATEGIES.values() if s.risk_level == risk_level]
```

---

## Phase 2: Modify Portfolio Optimizer for Backtesting

### Modify: `backend/app/services/portfolio_optimizer.py`

```python
class PortfolioOptimizerService:
    async def start_optimization(
        self,
        plan: Plan,
        historical_date: Optional[str] = None,  # NEW: ISO date string for backtesting
        use_strategy_template: Optional[str] = None,  # NEW: Strategy template ID
        ...
    ) -> str:
        """
        Start portfolio optimization
        
        Args:
            historical_date: If provided, optimize as if we were at this date (for backtesting)
            use_strategy_template: If provided, use pre-built strategy constraints
        """
        ...
```

### In `_run_optimization` method:

```python
async def _run_optimization(self, ...):
    # Determine data date range
    if historical_date:
        # Parse historical date
        hist_date = datetime.fromisoformat(historical_date)
        
        # Fetch extended history: (hist_date - 2 years) to NOW
        # We need data before hist_date for training, after for validation
        end_date = datetime.now()
        start_date = hist_date - timedelta(days=730)  # 2 years training
        
        all_data = await self.data_service.get_historical_data(
            tickers=plan.tickers,
            start_date=start_date,
            end_date=end_date,
            ...
        )
        
        # CRITICAL: Split into training (before hist_date) and test (after hist_date)
        training_data = all_data[all_data.index <= hist_date]
        test_data = all_data[all_data.index > hist_date]
        
        # Use only training data for optimization
        expected_returns = self._calculate_returns(training_data)
        cov_matrix = self._calculate_covariance(training_data)
        
        # Apply constraints (from strategy template or plan)
        if use_strategy_template:
            constraints = self.strategies_service.get_strategy(use_strategy_template).constraints
        else:
            constraints = plan.constraints
        
        # Run optimization
        result = self._optimize_mean_variance(expected_returns, cov_matrix, constraints)
        
        # NEW: Calculate backtest performance
        backtest_result = self._calculate_backtest_performance(
            optimal_weights=result.weights,
            test_data=test_data,
            initial_amount=plan.amount,
            historical_date=hist_date
        )
        
        result.backtest_result = backtest_result
        
    else:
        # Normal optimization (current behavior)
        ...
```

### New method: `_calculate_backtest_performance`

```python
def _calculate_backtest_performance(
    self,
    optimal_weights: Dict[str, float],
    test_data: pd.DataFrame,
    initial_amount: float,
    historical_date: datetime
) -> BacktestResult:
    """
    Calculate how the optimized portfolio would have performed
    
    Uses only forward-looking data (test_data) to validate the optimization
    """
    # Calculate daily portfolio returns
    portfolio_returns = (test_data['close'] * optimal_weights).sum(axis=1)
    
    # Calculate portfolio value over time
    portfolio_value = initial_amount * (1 + portfolio_returns).cumprod()
    
    # Calculate benchmark (e.g., 60/40 SPY/AGG)
    benchmark_weights = {'SPY': 0.6, 'AGG': 0.4}
    benchmark_returns = (test_data['close'] * benchmark_weights).sum(axis=1)
    benchmark_value = initial_amount * (1 + benchmark_returns).cumprod()
    
    # Calculate metrics
    total_return = (portfolio_value.iloc[-1] / initial_amount) - 1
    volatility = portfolio_returns.std() * np.sqrt(252)
    
    # Max drawdown
    rolling_max = portfolio_value.expanding().max()
    drawdown = (portfolio_value - rolling_max) / rolling_max
    max_drawdown = drawdown.min()
    
    # Recovery time (if drawdown occurred)
    recovery_date = None
    if max_drawdown < -0.05:  # 5% or more drop
        max_dd_date = drawdown.idxmin()
        recovery_mask = portfolio_value > portfolio_value.loc[max_dd_date]
        if recovery_mask.any():
            recovery_date = portfolio_value[recovery_mask].index[0]
    
    return BacktestResult(
        trajectory=[
            {'date': date, 'value': value} 
            for date, value in portfolio_value.items()
        ],
        benchmark_trajectory=[
            {'date': date, 'value': value} 
            for date, value in benchmark_value.items()
        ],
        metrics={
            'total_return': total_return,
            'volatility': volatility,
            'sharpe_ratio': (portfolio_returns.mean() / portfolio_returns.std()) * np.sqrt(252),
            'max_drawdown': max_drawdown,
            'recovery_days': (recovery_date - drawdown.idxmin()).days if recovery_date else None,
            'cagr': (portfolio_value.iloc[-1] / initial_amount) ** (1 / len(portfolio_value) * 252) - 1
        }
    )
```

---

## Phase 3: Data Models

### Modify: `backend/app/models/portfolio.py`

```python
from pydantic import BaseModel
from typing import Optional, List, Dict

class BacktestResult(BaseModel):
    """Results from historical backtest"""
    trajectory: List[Dict[str, Any]]  # [{'date': '2020-01-01', 'value': 10000}, ...]
    benchmark_trajectory: List[Dict[str, Any]]
    metrics: Dict[str, float]
    
    # For family investor context
    class Config:
        json_schema_extra = {
            "example": {
                "trajectory": [
                    {"date": "2020-01-01", "value": 10000},
                    {"date": "2020-03-23", "value": 7500},  # COVID crash
                    {"date": "2020-12-31", "value": 11500}
                ],
                "benchmark_trajectory": [...],
                "metrics": {
                    "total_return": 0.15,
                    "max_drawdown": -0.25,
                    "recovery_days": 180,
                    "volatility": 0.18,
                    "sharpe_ratio": 0.85,
                    "cagr": 0.14
                }
            }
        }

class OptimizationResult(BaseModel):
    """Extended to include backtesting"""
    # ... existing fields ...
    
    backtest_result: Optional[BacktestResult] = None  # NEW

class StrategyTemplateResponse(BaseModel):
    """API response for strategy template"""
    strategy_id: str
    name: str
    description: str
    risk_level: str
    icon: str
    tags: List[str]
    constraints_summary: Dict[str, Any]  # Human-readable summary
```

---

## Phase 4: API Endpoints

### New file: `backend/app/api/strategies.py`

```python
from fastapi import APIRouter, HTTPException
from app.services.strategies_service import StrategiesService

router = APIRouter(prefix="/api/strategies", tags=["strategies"])
strategies_service = StrategiesService()

@router.get("")
async def list_strategies(risk_level: Optional[str] = None):
    """List all available strategy templates"""
    if risk_level:
        return strategies_service.get_strategies_by_risk(risk_level)
    return strategies_service.get_all_strategies()

@router.get("/{strategy_id}")
async def get_strategy(strategy_id: str):
    """Get specific strategy template"""
    strategy = strategies_service.get_strategy(strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return strategy
```

### Modify: `backend/app/api/portfolio.py`

```python
@router.post("/optimize")
async def optimize_portfolio(
    request: OptimizationRequest,
    historical_date: Optional[str] = None,  # NEW
    use_strategy: Optional[str] = None  # NEW
):
    """
    Start portfolio optimization
    
    Query params:
        historical_date: ISO date string for backtesting (e.g., "2020-01-01")
        use_strategy: Strategy template ID to use
    """
    job_id = await optimizer_service.start_optimization(
        plan=request.plan,
        historical_date=historical_date,
        use_strategy_template=use_strategy,
        ...
    )
    return {"job_id": job_id}
```

---

## Phase 5: Frontend - Playground UI

### New component: `frontend/components/Playground.tsx`

```typescript
interface Mode {
  type: 'future' | 'historical';
}

interface HistoricalConfig {
  startDate: string;  // ISO date
  initialAmount: number;
  currency: string;
}

interface FutureConfig {
  stressTest?: {
    marketShock: number;  // -0.20 for 20% drop
    interestRateChange: number;
  };
}

export function Playground({ plan }: Props) {
  const [mode, setMode] = useState<Mode>({ type: 'future' });
  const [selectedStrategy, setSelectedStrategy] = useState<string | null>(null);
  const [backtestResult, setBacktestResult] = useState<BacktestResult | null>(null);
  
  return (
    <div className="flex flex-col gap-6">
      {/* Mode Selector */}
      <div className="tabs tabs-boxed">
        <button 
          className={`tab ${mode.type === 'future' ? 'tab-active' : ''}`}
          onClick={() => setMode({ type: 'future' })}
        >
          Future Simulation
        </button>
        <button 
          className={`tab ${mode.type === 'historical' ? 'tab-active' : ''}`}
          onClick={() => setMode({ type: 'historical' })}
        >
          Historical Replay
        </button>
      </div>
      
      {mode.type === 'historical' ? (
        <HistoricalReplay 
          plan={plan}
          selectedStrategy={selectedStrategy}
          onResult={setBacktestResult}
        />
      ) : (
        <FutureSimulation 
          plan={plan}
          selectedStrategy={selectedStrategy}
        />
      )}
      
      {backtestResult && (
        <BacktestResults result={backtestResult} />
      )}
    </div>
  );
}
```

### Component: `frontend/components/HistoricalReplay.tsx`

```typescript
export function HistoricalReplay({ plan, selectedStrategy, onResult }: Props) {
  const [startDate, setStartDate] = useState('2020-01-01');
  const [amount, setAmount] = useState(10000);
  const [loading, setLoading] = useState(false);
  
  // Preset periods for family investor
  const presetPeriods = [
    { label: 'Pre-COVID (Jan 2020)', date: '2020-01-01', icon: '🦠' },
    { label: 'Pre-2008 Crisis (Jan 2008)', date: '2008-01-01', icon: '📉' },
    { label: 'Post-COVID Recovery (Jan 2022)', date: '2022-01-01', icon: '💉' },
    { label: '5 Years Ago', date: format(subYears(new Date(), 5), 'yyyy-MM-dd'), icon: '📅' },
    { label: '10 Years Ago', date: format(subYears(new Date(), 10), 'yyyy-MM-dd'), icon: '📅' },
  ];
  
  const runBacktest = async () => {
    setLoading(true);
    const result = await api.optimizePortfolio(plan.id, {
      historical_date: startDate,
      use_strategy: selectedStrategy,
      amount
    });
    onResult(result.backtest_result);
    setLoading(false);
  };
  
  return (
    <div className="card bg-base-200 p-6">
      <h3 className="text-xl font-bold mb-4">🕰️ Historical Replay</h3>
      <p className="text-sm text-base-content/70 mb-6">
        See how this strategy would have performed starting from a specific date in the past.
      </p>
      
      {/* Preset Periods */}
      <div className="mb-4">
        <label className="label">Quick Select Historical Period</label>
        <div className="flex flex-wrap gap-2">
          {presetPeriods.map(preset => (
            <button
              key={preset.date}
              className={`btn btn-sm ${startDate === preset.date ? 'btn-primary' : 'btn-outline'}`}
              onClick={() => setStartDate(preset.date)}
            >
              {preset.icon} {preset.label}
            </button>
          ))}
        </div>
      </div>
      
      {/* Custom Date Picker */}
      <div className="form-control mb-4">
        <label className="label">Or Pick Custom Start Date</label>
        <input
          type="date"
          className="input input-bordered"
          value={startDate}
          onChange={(e) => setStartDate(e.target.value)}
          max={format(new Date(), 'yyyy-MM-dd')}
        />
      </div>
      
      {/* Amount Input */}
      <div className="form-control mb-6">
        <label className="label">Investment Amount</label>
        <input
          type="number"
          className="input input-bordered"
          value={amount}
          onChange={(e) => setAmount(Number(e.target.value))}
        />
      </div>
      
      {/* Strategy Selector */}
      <StrategySelector 
        selected={selectedStrategy}
        onSelect={setSelectedStrategy}
      />
      
      {/* Run Button */}
      <button
        className="btn btn-primary btn-block mt-4"
        onClick={runBacktest}
        disabled={loading}
      >
        {loading ? <span className="loading loading-spinner" /> : '▶️ Run Backtest'}
      </button>
    </div>
  );
}
```

### Component: `frontend/components/BacktestResults.tsx`

```typescript
export function BacktestResults({ result }: { result: BacktestResult }) {
  return (
    <div className="card bg-base-200 p-6">
      <h3 className="text-xl font-bold mb-6">📊 Backtest Results</h3>
      
      {/* Key Metrics - Family Investor Focused */}
      <div className="stats stats-vertical lg:stats-horizontal shadow mb-6">
        <div className="stat">
          <div className="stat-title">Final Value</div>
          <div className="stat-value text-primary">
            {formatCurrency(result.trajectory[result.trajectory.length - 1].value)}
          </div>
          <div className="stat-desc">
            {formatPercent(result.metrics.total_return)} total return
          </div>
        </div>
        
        <div className="stat">
          <div className="stat-title">Worst Case (Max Drawdown)</div>
          <div className="stat-value text-error">
            {formatPercent(result.metrics.max_drawdown)}
          </div>
          <div className="stat-desc">
            {result.metrics.recovery_days 
              ? `Recovered in ${result.metrics.recovery_days} days`
              : 'Never fully recovered'
            }
          </div>
        </div>
        
        <div className="stat">
          <div className="stat-title">Annualized Return</div>
          <div className="stat-value">
            {formatPercent(result.metrics.cagr)}
          </div>
          <div className="stat-desc">
            Per year (CAGR)
          </div>
        </div>
        
        <div className="stat">
          <div className="stat-title">Risk-Adjusted Return</div>
          <div className="stat-value">
            {result.metrics.sharpe_ratio.toFixed(2)}
          </div>
          <div className="stat-desc">
            Sharpe Ratio
          </div>
        </div>
      </div>
      
      {/* Chart */}
      <div className="h-96">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Legend />
            
            {/* Portfolio */}
            <Line 
              type="monotone" 
              dataKey="portfolio" 
              stroke="#2563eb" 
              strokeWidth={2}
              name="Your Portfolio"
            />
            
            {/* Benchmark */}
            <Line 
              type="monotone" 
              dataKey="benchmark" 
              stroke="#94a3b8" 
              strokeDasharray="5 5"
              name="Benchmark (60/40)"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      
      {/* Historical Event Markers */}
      <div className="mt-4">
        <h4 className="font-bold mb-2">📌 Key Historical Events</h4>
        <div className="flex flex-wrap gap-2">
          {getHistoricalEvents(result.trajectory[0].date, result.trajectory[result.trajectory.length - 1].date).map(event => (
            <div key={event.date} className="badge badge-outline badge-lg">
              {event.icon} {format(parseISO(event.date), 'MMM yyyy')}: {event.name}
            </div>
          ))}
        </div>
      </div>
      
      {/* Insights for Family Investor */}
      <div className="alert alert-info mt-6">
        <InfoIcon />
        <div>
          <h3 className="font-bold">How to Interpret This</h3>
          <div className="text-sm">
            <p>• If you invested on <strong>{format(parseISO(result.trajectory[0].date), 'MMM yyyy')}</strong>, you would have <strong>
              {result.metrics.total_return >= 0 ? 'gained' : 'lost'}
              {formatPercent(Math.abs(result.metrics.total_return))}
            </strong> by today.</p>
            <p>• The worst drop was <strong>{formatPercent(Math.abs(result.metrics.max_drawdown))}</strong>.</p>
            <p>• {result.metrics.recovery_days 
              ? `It took ${Math.floor(result.metrics.recovery_days / 30)} months to recover.`
              : 'The portfolio never fully recovered from its worst drop.'}</p>
          </div>
        </div>
      </div>
    </div>
  );
}

// Historical events data
const HISTORICAL_EVENTS = [
  { date: '2008-09-15', name: 'Lehman Collapse', icon: '🏦' },
  { date: '2020-03-11', name: 'COVID Declared', icon: '🦠' },
  { date: '2022-02-24', name: 'Ukraine War', icon: '💥' },
  { date: '2022-03-16', name: 'Fed Rate Hikes Begin', icon: '📈' },
];
```

---

## Testing Strategy

### Unit Tests: `backend/tests/test_backtest.py`

```python
import pytest
from datetime import datetime
from app.services.portfolio_optimizer import PortfolioOptimizerService

@pytest.mark.asyncio
async def test_backtest_no_forward_leak():
    """Ensure backtesting doesn't use future data"""
    optimizer = PortfolioOptimizerService()
    
    # Optimize as of Jan 1, 2020
    result = await optimizer.start_optimization(
        plan=test_plan,
        historical_date="2020-01-01"
    )
    
    # Should have backtest result
    assert result.backtest_result is not None
    
    # Trajectory should start AFTER historical date
    start_date = datetime.fromisoformat(result.backtest_result.trajectory[0]['date'])
    assert start_date > datetime.fromisoformat("2020-01-01")
    
    # Optimization should NOT know about COVID crash
    # (would likely have high equity allocation)
    assert any(w['ticker'] == 'SPY' and w['weight'] > 0.4 for w in result.optimal_portfolio)

@pytest.mark.asyncio
async def test_strategy_templates():
    """Test strategy template constraints are applied"""
    from app.services.strategies_service import StrategiesService
    
    service = StrategiesService()
    strategy = service.get_strategy("conservative_income")
    
    assert strategy.constraints.max_volatility == 0.10
    assert strategy.constraints.min_dividend_yield == 0.02
```

### Integration Test: `frontend/tests/playground.spec.ts`

```typescript
test('should run historical backtest for Jan 2020', async ({ page }) => {
  await page.goto('/plans/plan-1');
  
  // Click Playground tab
  await page.getByRole('tab', { name: 'Playground' }).click();
  
  // Select Historical Replay mode
  await page.getByRole('tab', { name: 'Historical Replay' }).click();
  
  // Select preset period
  await page.getByRole('button', { name: '🦠 Pre-COVID' }).click();
  
  // Click run
  await page.getByRole('button', { name: 'Run Backtest' }).click();
  
  // Wait for results
  await expect(page.getByText('Backtest Results')).toBeVisible();
  
  // Verify COVID crash is visible
  await expect(page.getByText('-30%')).toBeVisible();
  
  // Verify final value is positive (recovered)
  await expect(page.getByText(/\$1[12,]\d{3}/)).toBeVisible();
});
```

---

## Performance & Caching Strategy

### Cache Keys
```
backtest:{plan_id}:{strategy_id}:{historical_date}:{amount}
```

### Cache TTL
- Backtest results: 7 days (historical data doesn't change)
- Strategy templates: Never (static)

### Implementation
```python
# In portfolio_optimizer.py
cache_key = f"backtest:{plan.plan_id}:{use_strategy}:{historical_date}:{plan.amount}"
cached = await self.cache_service.get(cache_key)
if cached:
    return cached
```

---

## Rollout Plan

### Sprint 1 (Week 1-2): Foundation
- [ ] Add sector ETFs to config
- [ ] Create `StrategiesService` with 3-5 templates
- [ ] Add API endpoints for strategies
- [ ] Unit tests for strategies

### Sprint 2 (Week 3-4): Backtesting Core
- [ ] Modify `PortfolioOptimizer` to support `historical_date`
- [ ] Implement `_calculate_backtest_performance`
- [ ] Add `BacktestResult` model
- [ ] Prevent forward-looking bias (critical tests)
- [ ] Add caching

### Sprint 3 (Week 5-6): Frontend UI
- [ ] Build `Playground` component
- [ ] Build `HistoricalReplay` component
- [ ] Build `BacktestResults` component
- [ ] Build `StrategySelector` component
- [ ] Add historical events data

### Sprint 4 (Week 7-8): Polish & Launch
- [ ] E2E tests
- [ ] Performance optimization
- [ ] User documentation
- [ ] Beta testing with family investors
- [ ] Iterate based on feedback

---

## Success Metrics

1. **Engagement**: Users create 2+ scenarios on average
2. **Confidence**: Users who use backtesting show higher confidence (survey)
3. **Education**: Users can explain "max drawdown" after using the feature
4. **Conversion**: Users who backtest are more likely to invest

---

## Open Questions

1. **Rebalancing Frequency**: Should backtests rebalance monthly, quarterly, or never?
   - **Recommendation**: Start with quarterly (common practice)
   
2. **Dividends**: Should we reinvest dividends in backtests?
   - **Recommendation**: Yes, assume DRIP (Dividend Reinvestment Plan)
   
3. **Benchmark**: Use SPY, 60/40, or allow user to choose?
   - **Recommendation**: Default to 60/40 SPY/AGG, show comparison
   
4. **Transaction Costs**: Include in backtests?
   - **Recommendation**: Yes, use existing commission settings
   
5. **Tax Impact**: Include capital gains taxes?
   - **Recommendation**: Yes, implement using simplified model (see Tax Implementation below)

---

## Tax Implementation for Backtesting

### Overview
Capital gains tax is critical for accurate after-tax returns. We'll implement a simplified but realistic model.

### Tax Configuration

#### Add to: `backend/config/etf_config.yaml`

```yaml
# Tax settings for backtesting and optimization
tax_settings:
  # Default capital gains tax rates (can be overridden per account type)
  short_term_capital_gains_rate: 0.35  # Tax on holdings < 1 year
  long_term_capital_gains_rate: 0.15   # Tax on holdings >= 1 year

  # Account-specific overrides
  account_types:
    taxable:
      short_term_capital_gains_rate: 0.35
      long_term_capital_gains_rate: 0.15
    nisa_growth:
      short_term_capital_gains_rate: 0.0
      long_term_capital_gains_rate: 0.0
    nisa_general:
      short_term_capital_gains_rate: 0.0
      long_term_capital_gains_rate: 0.0
    ideco:
      short_term_capital_gains_rate: 0.0
      long_term_capital_gains_rate: 0.0  # Taxed on withdrawal (not included here)

  # Tax loss harvesting settings
  enable_tax_loss_harvesting: false  # Can be enabled later

  # Wash sale rule (US-specific, 30-day window)
  # For Japan, this is less strict, so we'll ignore for now
  wash_sale_window_days: 0

  # Default holding period for backtesting (simplified)
  # In reality, each asset would have its own purchase date
  default_holding_period_days: 365
```

#### Add to: `backend/app/services/config_service.py`

```python
def get_tax_settings(self) -> Dict[str, Any]:
    """Get tax settings for backtesting."""
    config = self._get_etf_config()
    return config.get('tax_settings', {
        "short_term_capital_gains_rate": 0.35,
        "long_term_capital_gains_rate": 0.15,
        "account_types": {
            "taxable": {
                "short_term_capital_gains_rate": 0.35,
                "long_term_capital_gains_rate": 0.15,
            },
            "nisa_growth": {
                "short_term_capital_gains_rate": 0.0,
                "long_term_capital_gains_rate": 0.0,
            }
        }
    })

def get_tax_rate_for_account(self, account_type: str, holding_period_days: int = 365) -> float:
    """
    Get applicable tax rate for account type and holding period.

    Args:
        account_type: 'taxable', 'nisa_growth', etc.
        holding_period_days: Days held (defaults to 1 year for long-term)

    Returns:
        Tax rate (e.g., 0.15 for 15%)
    """
    tax_settings = self.get_tax_settings()

    # Get account-specific rates
    if account_type in tax_settings.get('account_types', {}):
        account_rates = tax_settings['account_types'][account_type]
    else:
        account_rates = {
            'short_term_capital_gains_rate': tax_settings.get('short_term_capital_gains_rate', 0.35),
            'long_term_capital_gains_rate': tax_settings.get('long_term_capital_gains_rate', 0.15),
        }

    # Determine if short-term or long-term
    if holding_period_days >= 365:
        return account_rates.get('long_term_capital_gains_rate', 0.15)
    else:
        return account_rates.get('short_term_capital_gains_rate', 0.35)
```

### Tax Calculation Logic

#### Update: `_calculate_backtest_performance` method

```python
def _calculate_backtest_performance(
    self,
    optimal_weights: Dict[str, float],
    test_data: pd.DataFrame,
    initial_amount: float,
    historical_date: datetime,
    account_type: str = 'taxable',  # NEW
    holding_period_days: int = 365,  # NEW
) -> BacktestResult:
    """
    Calculate how the optimized portfolio would have performed (after taxes)
    """
    # Calculate pre-tax portfolio returns
    portfolio_returns = (test_data['close'] * optimal_weights).sum(axis=1)
    portfolio_value = initial_amount * (1 + portfolio_returns).cumprod()
    final_value = portfolio_value.iloc[-1]

    # Calculate pre-tax metrics
    pre_tax_total_return = (final_value / initial_amount) - 1

    # NEW: Calculate capital gains tax
    # Get tax rate from config
    tax_rate = self.config_service.get_tax_rate_for_account(
        account_type=account_type,
        holding_period_days=holding_period_days
    )

    # Calculate net capital gain (earnings - losses)
    # Note: This is simplified - in reality, you'd track each position's cost basis
    capital_gain = max(0, final_value - initial_amount)  # No tax if loss

    # Calculate tax liability
    capital_gains_tax = capital_gain * tax_rate

    # After-tax final value
    after_tax_final_value = final_value - capital_gains_tax
    after_tax_return = (after_tax_final_value / initial_amount) - 1

    # Calculate after-tax trajectory (tax only paid at end for simplicity)
    # For more accuracy, we'd calculate tax on each rebalance
    after_tax_trajectory = [
        {
            'date': date,
            'value': value if i < len(portfolio_value) - 1 else after_tax_final_value,
            'pre_tax_value': value,
        }
        for i, (date, value) in enumerate(zip(portfolio_value.index, portfolio_value))
    ]

    # Recalculate metrics on after-tax basis
    after_tax_returns = portfolio_returns.copy()
    # Adjust final return for tax impact
    after_tax_returns.iloc[-1] -= capital_gains_tax / final_value

    after_tax_volatility = after_tax_returns.std() * np.sqrt(252)

    # Recalculate drawdowns on after-tax basis
    after_tax_portfolio_value = pd.Series(
        [v['value'] for v in after_tax_trajectory],
        index=[pd.to_datetime(v['date']) for v in after_tax_trajectory]
    )
    rolling_max = after_tax_portfolio_value.expanding().max()
    drawdown = (after_tax_portfolio_value - rolling_max) / rolling_max
    max_drawdown = drawdown.min()

    return BacktestResult(
        trajectory=after_tax_trajectory,
        benchmark_trajectory=[...],  # Also calculate after-tax for benchmark
        metrics={
            # Pre-tax metrics (for comparison)
            'pre_tax_total_return': pre_tax_total_return,
            'pre_tax_final_value': final_value,

            # After-tax metrics
            'total_return': after_tax_return,
            'final_value': after_tax_final_value,
            'volatility': after_tax_volatility,
            'sharpe_ratio': (after_tax_returns.mean() / after_tax_returns.std()) * np.sqrt(252),
            'max_drawdown': max_drawdown,

            # Tax-specific metrics
            'capital_gains_tax': capital_gains_tax,
            'tax_rate': tax_rate,
            'tax_impact': capital_gains_tax / final_value if final_value > 0 else 0,  # Tax as % of value

            # Additional metrics
            'cagr': (after_tax_final_value / initial_amount) ** (1 / len(portfolio_value) * 252) - 1
        },
        account_type=account_type,  # Track which account type was used
    )
```

### Enhanced Tax Model (Optional - Phase 2)

For more accurate tax calculations, we can track each position's cost basis:

```python
@dataclass
class TaxLot:
    """Track individual tax lots for accurate capital gains"""
    ticker: str
    shares: float
    purchase_date: datetime
    cost_basis: float  # Total cost (price * shares + commission)

class TaxAwarePortfolio:
    """Portfolio that tracks tax lots for accurate capital gains"""

    def __init__(self, initial_amount: float, weights: Dict[str, float], prices: Dict[str, float]):
        self.tax_lots: Dict[str, List[TaxLot]] = {}
        self.cash = initial_amount

        # Create initial tax lots
        for ticker, weight in weights.items():
            investment = initial_amount * weight
            shares = investment / prices[ticker]
            self.tax_lots[ticker] = [
                TaxLot(
                    ticker=ticker,
                    shares=shares,
                    purchase_date=datetime.now(),
                    cost_basis=investment
                )
            ]

    def sell(self, ticker: str, shares_to_sell: float, current_price: float, current_date: datetime) -> float:
        """Sell shares and calculate capital gains tax"""
        lots = self.tax_lots[ticker]
        shares_remaining = shares_to_sell
        capital_gain = 0
        proceeds = 0

        for lot in lots[:]:  # Iterate over copy
            if shares_remaining <= 0:
                break

            # Use FIFO or specific lot identification
            shares_from_lot = min(lot.shares, shares_remaining)

            # Calculate proceeds
            lot_proceeds = shares_from_lot * current_price
            lot_cost = lot.cost_basis * (shares_from_lot / lot.shares)
            lot_gain = lot_proceeds - lot_cost

            capital_gain += lot_gain
            proceeds += lot_proceeds

            # Update lot
            lot.shares -= shares_from_lot
            if lot.shares <= 0:
                lots.remove(lot)

            shares_remaining -= shares_from_lot

        # Calculate tax based on holding period
        # (In reality, each lot has its own holding period)
        avg_holding_period = self._calculate_avg_holding_period(ticker)
        tax_rate = self.config_service.get_tax_rate_for_account(
            account_type='taxable',
            holding_period_days=avg_holding_period
        )

        tax = max(0, capital_gain) * tax_rate
        self.cash += proceeds - tax

        return tax

    def _calculate_avg_holding_period(self, ticker: str) -> int:
        """Calculate average holding period for remaining lots"""
        # Simplified - would track each lot's purchase date
        return 365  # Default to long-term
```

### UI Updates

#### Update: `frontend/components/BacktestResults.tsx`

```typescript
export function BacktestResults({ result }: { result: BacktestResult }) {
  const { metrics } = result;

  return (
    <div className="card bg-base-200 p-6">
      <h3 className="text-xl font-bold mb-6">📊 Backtest Results</h3>

      {/* Tax Comparison Toggle */}
      <div className="mb-6">
        <div className="alert alert-info">
          <InfoIcon />
          <div>
            <h3 className="font-bold">💰 After-Tax Returns</h3>
            <p className="text-sm">
              Results show <strong>after-tax</strong> performance for <span className="font-mono">{result.account_type}</span> account.
              Capital gains tax: <strong>{(metrics.tax_rate * 100).toFixed(1)}%</strong>
            </p>
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="stats stats-vertical lg:stats-horizontal shadow mb-6">
        <div className="stat">
          <div className="stat-title">Final Value (After Tax)</div>
          <div className="stat-value text-primary">
            {formatCurrency(metrics.final_value)}
          </div>
          <div className="stat-desc">
            {formatPercent(metrics.total_return)} after-tax return
          </div>
          {metrics.pre_tax_total_return !== metrics.total_return && (
            <div className="stat-desc text-error">
              {formatPercent(metrics.pre_tax_total_return)} pre-tax
            </div>
          )}
        </div>

        <div className="stat">
          <div className="stat-title">Capital Gains Tax</div>
          <div className="stat-value text-error">
            {formatCurrency(metrics.capital_gains_tax)}
          </div>
          <div className="stat-desc">
            {formatPercent(metrics.tax_impact)} of portfolio value
          </div>
        </div>

        <div className="stat">
          <div className="stat-title">Tax Impact</div>
          <div className="stat-value">
            {formatPercent(metrics.total_return - metrics.pre_tax_total_return)}
          </div>
          <div className="stat-desc">
            Drag from taxes
          </div>
        </div>

        {/* ... existing metrics ... */}
      </div>

      {/* Tax Insight Banner */}
      {metrics.capital_gains_tax > 0 && (
        <div className="alert alert-warning mb-6">
          <AlertTriangleIcon />
          <div>
            <h3 className="font-bold">Tax Efficiency Insight</h3>
            <p className="text-sm">
              This strategy generated <strong>{formatCurrency(metrics.capital_gains_tax)}</strong> in capital gains taxes.
              Consider using <span className="font-semibold">tax-advantaged accounts (NISA/iDeCo)</span> to improve after-tax returns.
              <br />
              <span className="text-xs">
                Potential savings in NISA: <strong>{formatCurrency(metrics.capital_gains_tax)}</strong> (0% tax rate)
              </span>
            </p>
          </div>
        </div>
      )}

      {/* Chart with toggle for pre-tax/after-tax */}
      <div className="h-96">
        <div className="flex justify-between items-center mb-4">
          <h4 className="font-bold">Portfolio Value Over Time</h4>
          <div className="join">
            <button className="btn btn-sm btn join-item">After Tax</button>
            <button className="btn btn-sm join-item">Pre-Tax</button>
          </div>
        </div>
        {/* ... chart ... */}
      </div>
    </div>
  );
}
```

### Account Type Selector

#### Add to: `frontend/components/HistoricalReplay.tsx`

```typescript
const ACCOUNT_TYPES = [
  { value: 'taxable', label: 'Taxable Account', taxRate: 20.315, icon: '💵' },
  { value: 'nisa_growth', label: 'NISA Growth', taxRate: 0, icon: '🆓' },
  { value: 'nisa_general', label: 'NISA General', taxRate: 0, icon: '🆓' },
  { value: 'ideco', label: 'iDeCo', taxRate: 0, icon: '🏛️' },
];

export function HistoricalReplay({ plan, selectedStrategy, onResult }: Props) {
  const [accountType, setAccountType] = useState('taxable');

  return (
    <div className="card bg-base-200 p-6">
      {/* ... existing fields ... */}

      {/* Account Type Selector */}
      <div className="form-control mb-6">
        <label className="label">Account Type (affects taxes)</label>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
          {ACCOUNT_TYPES.map(account => (
            <button
              key={account.value}
              className={`btn btn-sm ${accountType === account.value ? 'btn-primary' : 'btn-outline'}`}
              onClick={() => setAccountType(account.value)}
            >
              <span className="text-lg mr-1">{account.icon}</span>
              <span className="text-xs">{account.label}</span>
              <span className="badge badge-neutral badge-xs ml-1">{account.taxRate}%</span>
            </button>
          ))}
        </div>
        <label className="label">
          <span className="label-text-alt text-info">
            💡 Tip: NISA accounts have 0% capital gains tax
          </span>
        </label>
      </div>

      {/* Pass accountType to backtest */}
      <button
        className="btn btn-primary btn-block mt-4"
        onClick={() => runBacktest(accountType)}
        disabled={loading}
      >
        {loading ? <span className="loading loading-spinner" /> : '▶️ Run Backtest'}
      </button>
    </div>
  );
}
```

### Testing Tax Calculations

#### Add to: `backend/tests/test_backtest.py`

```python
@pytest.mark.asyncio
async def test_capital_gains_tax_calculation():
    """Test that capital gains tax is correctly calculated"""
    optimizer = PortfolioOptimizerService()

    result = await optimizer.start_optimization(
        plan=test_plan,
        historical_date="2020-01-01",
        account_type='taxable'
    )

    # Should have tax metrics
    assert result.backtest_result.metrics['capital_gains_tax'] > 0
    assert result.backtest_result.metrics['tax_rate'] == 0.15  # Long-term rate

    # After-tax return should be less than pre-tax
    assert result.backtest_result.metrics['total_return'] < result.backtest_result.metrics['pre_tax_total_return']

@pytest.mark.asyncio
async def test_nisa_tax_exemption():
    """Test that NISA accounts have 0% tax"""
    result = await optimizer.start_optimization(
        plan=test_plan,
        historical_date="2020-01-01",
        account_type='nisa_growth'
    )

    # Should have 0% tax
    assert result.backtest_result.metrics['tax_rate'] == 0.0
    assert result.backtest_result.metrics['capital_gains_tax'] == 0.0

    # After-tax should equal pre-tax
    assert result.backtest_result.metrics['total_return'] == result.backtest_result.metrics['pre_tax_total_return']
```

### User Education

The tax feature provides an excellent opportunity to educate users about tax-efficient investing:

```
Key Insights for Family Investors:

1. **Tax Drag**: Taxes can reduce returns by 15-35%
   - Example: ¥1M gain → ¥150K-¥350K in taxes

2. **Tax-Advantaged Accounts**: Use NISA/iDeCo first
   - NISA Growth: ¥1.8M/year tax-free
   - NISA General: ¥1.2M/year tax-free
   - iDeCo: Tax-deferred until withdrawal

3. **Holding Period**: Long-term gains (≥1 year) taxed at 15% vs 35% short-term
   - Encourages buy-and-hold strategy

4. **Tax Loss Harvesting**: Offset gains with losses (future feature)
   - Can reduce tax bill significantly
```

### Summary of Changes

1. **Config**: Add `tax_settings` to `etf_config.yaml`
2. **ConfigService**: Add `get_tax_settings()` and `get_tax_rate_for_account()`
3. **Backtest**: Update `_calculate_backtest_performance()` to calculate taxes
4. **Models**: Update `BacktestResult` to include tax metrics
5. **API**: Accept `account_type` parameter in optimization endpoint
6. **UI**: Add account type selector and display tax metrics
7. **Tests**: Verify tax calculations for different account types
