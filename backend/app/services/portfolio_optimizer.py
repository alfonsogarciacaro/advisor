import asyncio
import uuid
import datetime
import numpy as np
import pandas as pd
import scipy.optimize as sco
from typing import Dict, Any, List, Optional, Tuple
from app.services.history_service import HistoryService
from app.services.config_service import ConfigService
from app.services.storage_service import StorageService
from app.services.logger_service import LoggerService
from app.models.portfolio import OptimizationResult, PortfolioAsset, EfficientFrontierPoint, ScenarioForecast
from app.core.utils import sanitize_numpy

class PortfolioOptimizerService:
    def __init__(
        self,
        history_service: HistoryService,
        config_service: ConfigService,
        storage_service: StorageService,
        logger: LoggerService,
        forecasting_engine: Optional[Any] = None,
        llm_service: Optional[Any] = None
    ):
        self.history_service = history_service
        self.config_service = config_service
        self.storage_service = storage_service
        self.logger = logger
        self.forecasting_engine = forecasting_engine
        self.llm_service = llm_service
        self.collection = "optimization_jobs"

    async def start_optimization(self, amount: float, currency: str, excluded_tickers: List[str] = []) -> str:
        """Starts the optimization process in the background."""
        job_id = str(uuid.uuid4())
        
        initial_job_state = OptimizationResult(
            job_id=job_id,
            status="queued",
            created_at=datetime.datetime.now(datetime.timezone.utc),
            initial_amount=amount,
            currency=currency
        )
        
        await self.storage_service.save(self.collection, job_id, sanitize_numpy(initial_job_state.model_dump()))
        
        self.logger.info(f"Queuing optimization job {job_id} for amount {amount} {currency}")
        
        # Fire and forget task
        asyncio.create_task(self._run_optimization(job_id, amount, currency, excluded_tickers))
        
        return job_id

    async def _run_optimization(self, job_id: str, amount: float, currency: str, excluded_tickers: List[str]):
        try:
            self.logger.info(f"Starting optimization job {job_id}")
            # Update status
            await self._update_job_status(job_id, "fetching_data")

            # 1. Get ETF Universe
            all_etfs = self.config_service.get_all_etfs()
            tickers = [etf.symbol for etf in all_etfs if etf.symbol not in excluded_tickers]
            
            if not tickers:
                raise ValueError("No tickers available for optimization")

            # 2. Fetch Data (Price & Dividends)
            # We need daily returns for covariance matrix
            # We need dividend history for total return calculation
            
            # Fetch last 1 year of data for optimization
            period = "1y" 
            history_data = await self.history_service.get_historical_data(tickers, period=period)
            dividend_data = await self.history_service.get_dividend_history(tickers, period=period)
            
            # 3. Process Data
            prices_df = pd.DataFrame()
            dividends_total = {}
            
            for ticker in tickers:
                data = history_data.get(ticker, [])
                if not data:
                    continue
                    
                df = pd.DataFrame(data)
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                # Keep only close prices
                prices_df[ticker] = df['close']
                
                # Sum dividends
                divs = dividend_data.get(ticker, [])
                total_div = sum(d['amount'] for d in divs)
                dividends_total[ticker] = total_div

            # Drop missing data
            prices_df.dropna(inplace=True)

            if prices_df.empty or len(prices_df.columns) < 2:
                 raise ValueError("Insufficient data for optimization (correlation requires at least 2 assets with intersection)")

            valid_tickers = prices_df.columns.tolist()

            # Calculate Daily Returns for covariance matrix
            daily_returns = prices_df.pct_change().dropna()

            # Get expense ratios from config (needed for both forecast and historical paths)
            expense_ratios = {}
            for ticker in valid_tickers:
                etf_info = self.config_service.get_etf_info(ticker)
                expense_ratios[ticker] = etf_info.expense_ratio if etf_info and etf_info.expense_ratio else 0.0

            # Get Expected Returns from Forecasting Engine (or fall back to historical)
            if self.forecasting_engine:
                await self._update_job_status(job_id, "forecasting")

                # Use forecasting engine for forward-looking returns
                try:
                    forecast_result = await self.forecasting_engine.run_forecast_suite(
                        tickers=valid_tickers,
                        horizon="6mo",  # Use 6-month forecast
                        models=["gbm"], # disable "arima" for now to speed up testing
                        simulations=50,  # Lower sims for portfolio optimization speed
                        use_cache=True  # Use cached forecasts if available
                    )

                    # Extract expected returns from ensemble
                    expected_returns_dict = self.forecasting_engine.extract_expected_returns(forecast_result)

                    # Convert to pandas Series
                    expected_annual_returns = pd.Series(expected_returns_dict)

                    # Add dividend yields to forecast returns
                    current_prices = prices_df.iloc[-1]
                    dividend_yields = pd.Series(index=valid_tickers, dtype=float)
                    for ticker in valid_tickers:
                        price = current_prices[ticker]
                        div = dividends_total.get(ticker, 0.0)
                        dividend_yields[ticker] = div / price if price > 0 else 0.0

                    expected_annual_returns = expected_annual_returns + dividend_yields

                    # Subtract expense ratios from expected returns
                    for ticker in expected_annual_returns.index:
                        expected_annual_returns[ticker] -= expense_ratios.get(ticker, 0.0)

                except Exception as e:
                    # Fall back to historical returns if forecasting fails
                    self.logger.warning(f"Forecasting failed for job {job_id}, using historical returns: {e}")
                    expected_annual_returns = self._calculate_historical_returns(
                        daily_returns, prices_df, dividends_total, valid_tickers, expense_ratios
                    )
            else:
                # Use historical returns if no forecasting engine
                expected_annual_returns = self._calculate_historical_returns(
                    daily_returns, prices_df, dividends_total, valid_tickers, expense_ratios
                )
            
            # Covariance Matrix
            cov_matrix = daily_returns.cov() * 252
            
            # 4. Commission Handling
            comm_settings = self.config_service.get_commission_settings()
            # We will account for commission when calculating the final invested amount, 
            # but usually MVO doesn't optimize *for* commission unless it's a transaction cost model.
            # We will subtract estimated commission from the 'amount' to show 'Net Investment'.
            
            await self._update_job_status(job_id, "optimizing")
            
            # 5. Run MVO
            frontier, optimal = self._calculate_mean_variance(expected_annual_returns, cov_matrix)
            
            # 6. Format Result
            # Convert optimal weights to PortfolioAssets
            optimal_assets = []
            
            # Estimate Commission
            # Assume we buy all assets with weight > 1%
            active_assets = {k: v for k, v in optimal['weights'].items() if v > 0.001}
            num_trades = len(active_assets)
            
            total_commission = 0.0
            if comm_settings.get("type") == "flat_per_trade":
                total_commission = num_trades * comm_settings.get("value", 0.0)
            
            investable_amount = amount - total_commission
            if investable_amount < 0: investable_amount = 0
            
            for ticker, weight in active_assets.items():
                alloc_amount = investable_amount * weight
                metrics = await self.history_service.get_return_metrics([ticker]) # Get last price
                last_price = metrics[ticker]["last_price"]
                shares = alloc_amount / last_price if last_price > 0 else 0
                
                asset = PortfolioAsset(
                    ticker=ticker,
                    weight=weight,
                    amount=alloc_amount,
                    shares=shares,
                    price=last_price,
                    expected_return=expected_annual_returns[ticker],
                    annual_expense_ratio=expense_ratios.get(ticker, 0.0),
                    contribution_to_risk=0.0 # TODO: Calculate risk contribution
                )
                optimal_assets.append(asset)

            # 7. Generate Scenarios and LLM Report
            await self._update_job_status(job_id, "generating_analysis")

            scenarios = await self._generate_scenario_forecasts(
                optimal_weights=active_assets,
                investable_amount=investable_amount,
                valid_tickers=valid_tickers,
                expected_annual_returns=expected_annual_returns,
                cov_matrix=cov_matrix
            )

            llm_report = None
            if self.llm_service:
                llm_report = await self._generate_llm_report(
                    amount=amount,
                    currency=currency,
                    optimal_assets=optimal_assets,
                    metrics={
                        "total_commission": total_commission,
                        "net_investment": investable_amount,
                        "annual_custody_cost": sum(investable_amount * w * expense_ratios.get(t, 0.0) for t, w in active_assets.items()),
                        "expected_annual_return": optimal["annual_return"],
                        "annual_volatility": optimal["annual_volatility"],
                        "sharpe_ratio": optimal["sharpe_ratio"]
                    },
                    scenarios=scenarios
                )

            # 8. Save Result
            final_job_state = OptimizationResult(
                job_id=job_id,
                status="completed",
                created_at=datetime.datetime.now(datetime.timezone.utc), # Placeholder, should keep original
                completed_at=datetime.datetime.now(datetime.timezone.utc),
                initial_amount=amount,
                currency=currency,
                optimal_portfolio=optimal_assets,
                efficient_frontier=frontier,
                metrics={
                    "total_commission": total_commission,
                    "net_investment": investable_amount,
                    "annual_custody_cost": sum(investable_amount * w * expense_ratios.get(t, 0.0) for t, w in active_assets.items()),
                    "expected_annual_return": optimal["annual_return"],
                    "annual_volatility": optimal["annual_volatility"],
                    "sharpe_ratio": optimal["sharpe_ratio"]
                },
                scenarios=[s.model_dump() for s in scenarios],
                llm_report=llm_report
            )
            
            # Update with merge=True? StorageService replace for now.
            # Need to re-read creating_at? No, I'll just overwrite for simplicity or use the update method if available.
            # Base class generic update? 
            # Let's just save the full object.
            
            await self.storage_service.save(self.collection, job_id, sanitize_numpy(final_job_state.model_dump()))

        except Exception as e:
            self.logger.error(f"Optimization failed for job {job_id}: {e}")
            # Save error state
            error_state = {
                "job_id": job_id,
                "status": "failed",
                "error": str(e),
                "initial_amount": amount,
                "currency": currency,
                "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
            await self.storage_service.save(self.collection, job_id, sanitize_numpy(error_state))

    async def _update_job_status(self, job_id: str, status: str):
        # Fetch current, update status, save
        current = await self.storage_service.get(self.collection, job_id)
        if current:
            current["status"] = status
            await self.storage_service.save(self.collection, job_id, current)

    def _calculate_historical_returns(
        self,
        daily_returns: pd.DataFrame,
        prices_df: pd.DataFrame,
        dividends_total: Dict[str, float],
        valid_tickers: List[str],
        expense_ratios: Dict[str, float]
    ) -> pd.Series:
        """
        Calculate historical returns as fallback when forecasting is not available.

        Uses historical price returns plus dividend yields, minus expense ratios.
        """
        # Calculate historical annual returns from daily returns
        avg_daily_return = daily_returns.mean()
        annualized_price_return = avg_daily_return * 252

        # Add dividend yields
        current_prices = prices_df.iloc[-1]
        dividend_yields = pd.Series(index=valid_tickers, dtype=float)
        for ticker in valid_tickers:
            price = current_prices[ticker]
            div = dividends_total.get(ticker, 0.0)
            dividend_yields[ticker] = div / price if price > 0 else 0.0

        total_returns = annualized_price_return + dividend_yields

        # Subtract expense ratios
        for ticker in total_returns.index:
            total_returns[ticker] -= expense_ratios.get(ticker, 0.0)

        return total_returns

    def _calculate_mean_variance(self, mean_returns: pd.Series, cov_matrix: pd.DataFrame) -> Tuple[List[EfficientFrontierPoint], Dict[str, Any]]:
        num_assets = len(mean_returns)
        args = (mean_returns.values, cov_matrix.values)
        tickers = mean_returns.index.tolist()
        risk_free_rate = 0.04 # Config?

        def portfolio_volatility(weights, mean_returns, cov_matrix):
            return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

        def portfolio_return(weights, mean_returns, cov_matrix):
            return np.sum(mean_returns * weights)

        def neg_sharpe_ratio(weights, mean_returns, cov_matrix):
            p_ret = portfolio_return(weights, mean_returns, cov_matrix)
            p_vol = portfolio_volatility(weights, mean_returns, cov_matrix)
            return -(p_ret - risk_free_rate) / p_vol

        constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
        bounds = tuple((0.0, 1.0) for asset in range(num_assets))

        # 1. Max Sharpe Ratio
        result_max_sharpe = sco.minimize(neg_sharpe_ratio, num_assets*[1./num_assets,], args=args,
                                    method='SLSQP', bounds=bounds, constraints=constraints)
        
        max_sharpe_weights = dict(zip(tickers, result_max_sharpe.x))
        max_sharpe_ret = portfolio_return(result_max_sharpe.x, mean_returns.values, cov_matrix.values)
        max_sharpe_vol = portfolio_volatility(result_max_sharpe.x, mean_returns.values, cov_matrix.values)
        
        optimal_portfolio = {
            "annual_return": max_sharpe_ret,
            "annual_volatility": max_sharpe_vol,
            "sharpe_ratio": (max_sharpe_ret - risk_free_rate) / max_sharpe_vol,
            "weights": max_sharpe_weights
        }

        # 2. Efficient Frontier
        # Find Min Vol and Max Ret portfolios to define range
        
        # Min Volatility
        def volatility_fun(weights, mean_returns, cov_matrix):
            return portfolio_volatility(weights, mean_returns, cov_matrix)
            
        result_min_vol = sco.minimize(volatility_fun, num_assets*[1./num_assets,], args=args,
                                    method='SLSQP', bounds=bounds, constraints=constraints)
        
        min_ret = portfolio_return(result_min_vol.x, mean_returns.values, cov_matrix.values)
        max_ret = mean_returns.max() # Theoretical max return is investing 100% in highest return asset
        
        target_returns = np.linspace(min_ret, max_ret, 20)
        efficient_frontier = []
        
        for target in target_returns:
            constraints_ef = (
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
                {'type': 'eq', 'fun': lambda x: portfolio_return(x, mean_returns.values, cov_matrix.values) - target}
            )
            
            result = sco.minimize(volatility_fun, num_assets*[1./num_assets,], args=args,
                                method='SLSQP', bounds=bounds, constraints=constraints_ef)
            
            if result.success:
                vol = result.fun # Minimized volatility
                ret = target
                sharpe = (ret - risk_free_rate) / vol
                weights = dict(zip(tickers, result.x))
                
                # Filter small weights
                weights = {k: v for k, v in weights.items() if v > 0.0001}
                
                point = EfficientFrontierPoint(
                    annual_volatility=vol,
                    annual_return=ret,
                    sharpe_ratio=sharpe,
                    weights=weights
                )
                efficient_frontier.append(point)
                
        return efficient_frontier, optimal_portfolio

    async def _generate_scenario_forecasts(
        self,
        optimal_weights: Dict[str, float],
        investable_amount: float,
        valid_tickers: List[str],
        expected_annual_returns: pd.Series,
        cov_matrix: pd.DataFrame
    ) -> List[ScenarioForecast]:
        """Generate scenario-based forecasts for the optimal portfolio."""
        scenarios = []

        # Base case - use the expected returns as-is
        base_return = sum(optimal_weights[t] * expected_annual_returns[t] for t in valid_tickers if t in optimal_weights)
        base_variance = 0
        for i, t1 in enumerate(valid_tickers):
            if t1 not in optimal_weights: continue
            for j, t2 in enumerate(valid_tickers):
                if t2 not in optimal_weights: continue
                base_variance += optimal_weights[t1] * optimal_weights[t2] * cov_matrix.iloc[i, j]
        base_volatility = np.sqrt(base_variance)

        def generate_trajectory(amount: float, annual_ret: float, months: int = 60) -> List[Dict[str, Any]]:
            traj = []
            start_date = datetime.datetime.now(datetime.timezone.utc)
            for i in range(months + 1):
                # Approximation of months for display purposes
                date = start_date + datetime.timedelta(days=30*i)
                val = amount * ((1 + annual_ret) ** (i / 12))
                traj.append({
                    "date": date.isoformat(),
                    "value": val
                })
            return traj

        # Base Case
        scenarios.append(ScenarioForecast(
            name="Base Case",
            probability=0.60,
            description="Expected market conditions with moderate growth and volatility.",
            expected_portfolio_value=investable_amount * (1 + base_return),
            expected_return=base_return,
            annual_volatility=base_volatility,
            trajectory=generate_trajectory(investable_amount, base_return)
        ))

        # Bull case - optimistic scenario
        bull_return = base_return * 1.5
        bull_volatility = base_volatility * 0.8
        
        scenarios.append(ScenarioForecast(
            name="Bull Case",
            probability=0.20,
            description="Optimistic scenario with strong market performance and lower volatility.",
            expected_portfolio_value=investable_amount * (1 + bull_return),
            expected_return=bull_return,
            annual_volatility=bull_volatility,
            trajectory=generate_trajectory(investable_amount, bull_return)
        ))

        # Bear case - pessimistic scenario
        bear_return = base_return * 0.3
        bear_volatility = base_volatility * 1.3

        scenarios.append(ScenarioForecast(
            name="Bear Case",
            probability=0.20,
            description="Pessimistic scenario with market downturns and elevated volatility.",
            expected_portfolio_value=investable_amount * (1 + bear_return),
            expected_return=bear_return,
            annual_volatility=bear_volatility,
            trajectory=generate_trajectory(investable_amount, bear_return)
        ))

        return scenarios

    async def _generate_llm_report(
        self,
        amount: float,
        currency: str,
        optimal_assets: List[PortfolioAsset],
        metrics: Dict[str, float],
        scenarios: List[ScenarioForecast]
    ) -> Optional[str]:
        """Generate an LLM-powered analysis report for the portfolio."""
        if not self.llm_service:
            return None

        import json

        portfolio_summary = {
            "initial_investment": f"{amount:.2f} {currency}",
            "net_investment": f"{metrics.get('net_investment', 0):.2f} {currency}",
            "expected_annual_return": f"{metrics.get('expected_annual_return', 0) * 100:.2f}%",
            "annual_volatility": f"{metrics.get('annual_volatility', 0) * 100:.2f}%",
            "sharpe_ratio": f"{metrics.get('sharpe_ratio', 0):.2f}",
            "num_holdings": len(optimal_assets),
            "top_holdings": [
                {
                    "ticker": a.ticker,
                    "weight": f"{a.weight * 100:.1f}%",
                    "amount": f"{a.amount:.2f} {currency}",
                    "expected_return": f"{a.expected_return * 100:.2f}%"
                }
                for a in sorted(optimal_assets, key=lambda x: x.weight, reverse=True)[:5]
            ],
            "scenarios": [
                {
                    "name": s.name,
                    "probability": f"{s.probability * 100:.0f}%",
                    "expected_value": f"{s.expected_portfolio_value:.2f} {currency}",
                    "expected_return": f"{s.expected_return * 100:.2f}%",
                    "volatility": f"{s.annual_volatility * 100:.2f}%"
                }
                for s in scenarios
            ]
        }

        prompt = f"""You are a financial advisor providing a portfolio analysis report. Analyze the following optimized portfolio:

Portfolio Summary:
{json.dumps(portfolio_summary, indent=2)}

Please provide a concise report (3-4 paragraphs) covering:
1. Portfolio Overview - Brief summary of the allocation strategy
2. Risk Analysis - Assessment of volatility and diversification
3. Return Expectations - Analysis of expected returns under different scenarios
4. Recommendations - Key considerations for the investor

Keep the tone professional yet accessible. Use markdown formatting for readability."""

        try:
            report = await self.llm_service.generate_response(prompt, use_cache=True)
            return report
        except Exception as e:
            self.logger.error(f"Failed to generate LLM report for job {job_id}: {e}")
            return None
