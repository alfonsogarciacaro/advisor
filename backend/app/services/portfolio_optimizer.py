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
from app.models.portfolio import OptimizationResult, PortfolioAsset, EfficientFrontierPoint

class PortfolioOptimizerService:
    def __init__(self, history_service: HistoryService, config_service: ConfigService, storage_service: StorageService):
        self.history_service = history_service
        self.config_service = config_service
        self.storage_service = storage_service
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
        
        await self.storage_service.save(self.collection, job_id, initial_job_state.model_dump())
        
        # Fire and forget task
        asyncio.create_task(self._run_optimization(job_id, amount, currency, excluded_tickers))
        
        return job_id

    async def _run_optimization(self, job_id: str, amount: float, currency: str, excluded_tickers: List[str]):
        try:
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

            # Calculate Daily Returns
            daily_returns = prices_df.pct_change().dropna()
            
            # Calculate Expected Annual Returns (Total Return = Price Change + Yield)
            # Price Return: (Last - First) / First  <-- Simple return over period
            # Or Compound Annual Growth Rate (CAGR)
            # Or Mean Daily Return * 252
            
            # Using Mean Daily Return * 252 usually assumes rebalancing or log returns. 
            # Let's use simple historical mean for now as a proxy for expected return
            avg_daily_return = daily_returns.mean()
            annualized_price_return = avg_daily_return * 252
            
            # Add Dividend Yield
            # Yield = Total Dividends / Price at beginning of period? Or Average Price?
            # Standard: Yield = Sum Dividends / Current Price (Forward Yield)
            # Or: Yield = Sum Dividends / Price 1 year ago (Trailing Yield)
            # Let's use Trailing Yield based on last price for forward expectation
            current_prices = prices_df.iloc[-1]
            
            dividend_yields = pd.Series(index=valid_tickers, dtype=float)
            for ticker in valid_tickers:
                price = current_prices[ticker]
                div = dividends_total.get(ticker, 0.0)
                dividend_yields[ticker] = div / price if price > 0 else 0.0
            
            expected_annual_returns = annualized_price_return + dividend_yields
            
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
                    contribution_to_risk=0.0 # TODO: Calculate risk contribution
                )
                optimal_assets.append(asset)
            
            # 7. Save Result
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
                    "expected_annual_return": optimal["annual_return"],
                    "annual_volatility": optimal["annual_volatility"],
                    "sharpe_ratio": optimal["sharpe_ratio"]
                }
            )
            
            # Update with merge=True? StorageService replace for now.
            # Need to re-read creating_at? No, I'll just overwrite for simplicity or use the update method if available.
            # Base class generic update? 
            # Let's just save the full object.
            
            await self.storage_service.save(self.collection, job_id, final_job_state.model_dump())

        except Exception as e:
            print(f"Optimization failed: {e}")
            # Save error state
            error_state = {
                "job_id": job_id,
                "status": "failed",
                "error": str(e),
                "initial_amount": amount,
                "currency": currency,
                "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
            await self.storage_service.save(self.collection, job_id, error_state)

    async def _update_job_status(self, job_id: str, status: str):
        # Fetch current, update status, save
        current = await self.storage_service.get(self.collection, job_id)
        if current:
            current["status"] = status
            await self.storage_service.save(self.collection, job_id, current)

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
