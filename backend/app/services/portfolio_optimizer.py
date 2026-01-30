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
from app.models.plan import PortfolioConstraints
from app.core.utils import sanitize_numpy
from app.core.prompt_manager import get_prompt_manager


class PortfolioOptimizerService:
    def __init__(
        self,
        history_service: HistoryService,
        config_service: ConfigService,
        storage_service: StorageService,
        logger: LoggerService,
        currency_service: Optional[Any] = None,
        forecasting_engine: Optional[Any] = None,
        llm_service: Optional[Any] = None,
        macro_service: Optional[Any] = None,
        risk_calculator: Optional[Any] = None
    ):
        self.history_service = history_service
        self.config_service = config_service
        self.storage_service = storage_service
        self.logger = logger
        self.currency_service = currency_service
        self.forecasting_engine = forecasting_engine
        self.llm_service = llm_service
        self.macro_service = macro_service
        self.risk_calculator = risk_calculator
        self.collection = "optimization_jobs"
        self.prompt_manager = get_prompt_manager()

    async def start_optimization(
        self,
        amount: float,
        currency: str,
        excluded_tickers: List[str] = [],
        plan_id: Optional[str] = None,
        fast: bool = False,
        historical_date: Optional[str] = None,
        use_strategy_template: Optional[str] = None,
        account_type: Optional[str] = None
    ) -> str:
        """
        Starts the optimization process in the background.

        Args:
            amount: Investment amount
            currency: Currency code
            excluded_tickers: Tickers to exclude from optimization
            plan_id: Optional plan ID to load constraints from
            fast: Use fast mode (skip forecasting, LLM, reduce simulations)
            historical_date: ISO date string for backtesting (e.g., "2020-01-01")
            use_strategy_template: Strategy template ID to use (e.g., "conservative_income")
            account_type: Account type for tax calculations (e.g., "taxable", "nisa_growth")
        """
        job_id = str(uuid.uuid4())

        # Load constraints from plan if provided
        constraints = None
        if plan_id and self.storage_service:
            try:
                plan_data = await self.storage_service.get("plans", plan_id)
                if plan_data and plan_data.get("constraints"):
                    # Convert dict back to PortfolioConstraints
                    constraints = PortfolioConstraints(**plan_data["constraints"])
            except Exception as e:
                self.logger.warning(f"Could not load constraints from plan {plan_id}: {e}")

        # Load constraints from strategy template if specified
        if use_strategy_template:
            try:
                from app.services.strategies_service import StrategiesService
                strategies_service = StrategiesService(self.config_service)
                template = strategies_service.get_strategy(use_strategy_template)
                if template:
                    # Convert template constraints to PortfolioConstraints
                    constraints = PortfolioConstraints(**template.constraints)
                    self.logger.info(f"Loaded constraints from strategy template: {use_strategy_template}")
            except Exception as e:
                self.logger.warning(f"Could not load strategy template {use_strategy_template}: {e}")

        initial_job_state = OptimizationResult(
            job_id=job_id,
            status="queued",
            created_at=datetime.datetime.now(datetime.timezone.utc),
            initial_amount=amount,
            currency=currency
        )

        await self.storage_service.save(self.collection, job_id, sanitize_numpy(initial_job_state.model_dump()))

        self.logger.info(f"Queuing optimization job {job_id} for amount {amount} {currency}")
        if historical_date:
            self.logger.info(f"Backtesting mode: historical_date={historical_date}")

        # Fire and forget task
        asyncio.create_task(self._run_optimization(
            job_id, amount, currency, excluded_tickers, constraints, fast,
            historical_date, use_strategy_template, account_type
        ))

        return job_id

    async def _run_optimization(
        self,
        job_id: str,
        amount: float,
        currency: str,
        excluded_tickers: List[str],
        constraints: Optional[PortfolioConstraints] = None,
        fast: bool = False,
        historical_date: Optional[str] = None,
        use_strategy_template: Optional[str] = None,
        account_type: Optional[str] = None
    ):
        try:
            self.logger.info(f"Starting optimization job {job_id}")
            if constraints:
                self.logger.info(f"Constraints applied: {constraints}")
            # Update status
            await self._update_job_status(job_id, "fetching_data")

            # 1. Get ETF Universe
            all_etfs = self.config_service.get_all_etfs()
            tickers = [etf.symbol for etf in all_etfs if etf.symbol not in excluded_tickers]
            
            if not tickers:
                raise ValueError("No tickers available for optimization")

            # 2. Fetch Data (Price & Dividends)
            # For backtesting, we need extended historical data
            if historical_date:
                # Backtesting mode: Fetch data from historical_date to NOW
                try:
                    hist_date = datetime.datetime.fromisoformat(historical_date)
                except ValueError:
                    raise ValueError(f"Invalid historical_date format: {historical_date}. Use YYYY-MM-DD.")

                # Fetch extended history: (hist_date - 2 years) to NOW
                # We need data before hist_date for training, after for validation
                end_date = datetime.datetime.now(datetime.timezone.utc)
                start_date = hist_date - datetime.timedelta(days=730)  # 2 years training

                # Calculate period in days for history service
                days_diff = (end_date - start_date).days
                period = "max" if days_diff > 365 * 5 else f"{days_diff // 30}mo"

                self.logger.info(f"Backtesting mode: Fetching {period} of data from {start_date.date()} to {end_date.date()}")
            else:
                # Normal optimization mode
                period = "1y"
                self.logger.info("Normal optimization mode: Fetching 1y of data")

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

            # NEW: For backtesting, split into training and test sets
            test_data = None
            if historical_date:
                hist_date = datetime.datetime.fromisoformat(historical_date)
                # Ensure hist_date is timezone-aware
                if hist_date.tzinfo is None:
                    hist_date = hist_date.replace(tzinfo=datetime.timezone.utc)

                # Training data: everything up to historical_date
                training_data = prices_df[prices_df.index <= hist_date]
                # Test data: everything after historical_date (for backtest validation)
                test_data = prices_df[prices_df.index > hist_date]

                if training_data.empty:
                    raise ValueError(f"Insufficient training data before {historical_date}")
                if test_data.empty:
                    raise ValueError(f"Insufficient test data after {historical_date}")

                self.logger.info(f"Training data: {training_data.index.min().date()} to {training_data.index.max().date()}")
                self.logger.info(f"Test data: {test_data.index.min().date()} to {test_data.index.max().date()}")

                # Use training data for optimization
                prices_for_optimization = training_data
            else:
                # Normal mode: use all data
                prices_for_optimization = prices_df
                test_data = None

            # Calculate Daily Returns for covariance matrix (using training data for backtesting)
            daily_returns = prices_for_optimization.pct_change().dropna()

            # Get expense ratios from config (needed for both forecast and historical paths)
            expense_ratios = {}
            for ticker in prices_for_optimization.columns.tolist():
                etf_info = self.config_service.get_etf_info(ticker)
                expense_ratios[ticker] = etf_info.expense_ratio if etf_info and etf_info.expense_ratio else 0.0

            # Get Expected Returns from Forecasting Engine (or fall back to historical)
            # Skip forecasting in fast mode to speed up tests
            if self.forecasting_engine and not fast:
                await self._update_job_status(job_id, "forecasting")

                # Use forecasting engine for forward-looking returns
                try:
                    forecast_result = await self.forecasting_engine.run_forecast_suite(
                        tickers=valid_tickers,
                        horizon="6mo",  # Use 6-month forecast
                        models=["gbm", "arima"],
                        simulations=10 if fast else 100,  # Fewer simulations in fast mode
                        model_params={"arima": {"auto_tune": False}},  # Disable auto-tuning for speed
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
                # Use historical returns if no forecasting engine or in fast mode
                if fast:
                    self.logger.info(f"Fast mode enabled for job {job_id}, skipping forecasting")
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

            # 5. Run MVO (with or without constraints)
            if constraints:
                frontier, optimal = self._calculate_mean_variance_constrained(
                    expected_annual_returns, cov_matrix, constraints, fast
                )
            else:
                frontier, optimal = self._calculate_mean_variance(expected_annual_returns, cov_matrix, fast)
            
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

            # 8. Run backtest if in historical mode
            backtest_result = None
            if historical_date and test_data is not None:
                self.logger.info(f"Calculating backtest performance from {historical_date}")
                try:
                    backtest_result = self._calculate_backtest_performance(
                        optimal_weights=active_assets,
                        test_data=test_data,
                        training_data=prices_for_optimization,
                        initial_amount=amount,
                        historical_date=datetime.datetime.fromisoformat(historical_date),
                        account_type=account_type or 'taxable'
                    )
                    self.logger.info(f"Backtest complete: {backtest_result.metrics['total_return']:.2%} return")
                except Exception as e:
                    self.logger.error(f"Backtest calculation failed: {e}")
                    # Don't fail the optimization, just skip backtest
                    backtest_result = None

            # 9. Calculate metrics
            metrics_dict = {
                "total_commission": total_commission,
                "net_investment": investable_amount,
                "annual_custody_cost": sum(investable_amount * w * expense_ratios.get(t, 0.0) for t, w in active_assets.items()),
                "expected_annual_return": optimal["annual_return"],
                "annual_volatility": optimal["annual_volatility"],
                "sharpe_ratio": optimal["sharpe_ratio"]
            }

            # 10. Save Result (Before LLM)
            final_job_state = OptimizationResult(
                job_id=job_id,
                status="generating_analysis",
                created_at=datetime.datetime.now(datetime.timezone.utc),
                completed_at=datetime.datetime.now(datetime.timezone.utc),
                initial_amount=amount,
                currency=currency,
                optimal_portfolio=optimal_assets,
                efficient_frontier=frontier,
                metrics=metrics_dict,
                scenarios=[s.model_dump() for s in scenarios], # type: ignore
                llm_report=None,
                backtest_result=sanitize_numpy(backtest_result.model_dump()) if backtest_result else None  # NEW
            )
            
            await self.storage_service.save(self.collection, job_id, sanitize_numpy(final_job_state.model_dump()))

            # 9. Generate LLM Report (skip LLM in fast mode, but provide basic suggestions)
            if self.llm_service and not fast:
                llm_result = await self._generate_llm_report(
                    amount=amount,
                    currency=currency,
                    optimal_assets=optimal_assets,
                    metrics=metrics_dict,
                    scenarios=scenarios
                )

                if llm_result:
                    # Store the report in llm_report
                    final_job_state.llm_report = llm_result.get("report", "")
                    # Store follow_up_suggestions in metrics for later access
                    metrics_dict["follow_up_suggestions"] = llm_result.get("follow_up_suggestions", [])
                    # Store constraint_suggestions if present
                    if "constraint_suggestions" in llm_result:
                        metrics_dict["constraint_suggestions"] = llm_result.get("constraint_suggestions", [])
            elif fast:
                # In fast mode, generate simple follow-up suggestions for testing
                self.logger.info(f"Fast mode: generating basic follow-up suggestions")
                metrics_dict["follow_up_suggestions"] = [
                    "Explain the expected return and volatility of this portfolio",
                    "Analyze the risk factors and diversification benefits",
                    "How would a recession scenario affect this portfolio?",
                    "What are the tax implications of this allocation?"
                ]
            
            # Final completion update
            final_job_state.status = "completed"
            if backtest_result:
                final_job_state.backtest_result = sanitize_numpy(backtest_result.model_dump())
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

    def _generate_trajectory(self, amount: float, annual_ret: float, months: int = 60) -> List[Dict[str, Any]]:
        """Generate a trajectory for scenario visualization."""
        traj = []
        start_date = datetime.datetime.now(datetime.timezone.utc)
        for i in range(months + 1):
            date = start_date + datetime.timedelta(days=30*i)
            val = amount * ((1 + annual_ret) ** (i / 12))
            traj.append({
                "date": date.isoformat(),
                "value": val
            })
        return traj

    async def _generate_llm_scenarios(
        self,
        optimal_weights: Dict[str, float],
        investable_amount: float,
        valid_tickers: List[str],
        expected_annual_returns: pd.Series,
        cov_matrix: pd.DataFrame
    ) -> Optional[List[ScenarioForecast]]:
        """Generate LLM-powered scenarios with context about the portfolio."""
        import json

        # Calculate portfolio-level metrics
        portfolio_return = sum(optimal_weights[t] * expected_annual_returns[t] for t in valid_tickers if t in optimal_weights)

        # Calculate portfolio volatility
        portfolio_variance: float = 0
        for i, t1 in enumerate(valid_tickers):
            if t1 not in optimal_weights: continue
            for j, t2 in enumerate(valid_tickers):
                if t2 not in optimal_weights: continue
                portfolio_variance += optimal_weights[t1] * optimal_weights[t2] * cov_matrix.iloc[i, j]  # type: ignore
        portfolio_volatility = np.sqrt(portfolio_variance)

        # Build context for LLM
        portfolio_context = {
            "total_investment": f"{investable_amount:.2f}",
            "expected_annual_return": f"{portfolio_return:.2%}",
            "annual_volatility": f"{portfolio_volatility:.2%}",
            "num_holdings": len(optimal_weights),
            "top_holdings": [
                {"ticker": t, "weight": f"{w:.1%}", "expected_return": f"{expected_annual_returns[t]:.2%}"}
                for t, w in sorted(optimal_weights.items(), key=lambda x: x[1], reverse=True)[:5]
            ]
        }

        prompt = self.prompt_manager.render_prompt(
            "portfolio_optimizer/scenario_analysis.jinja",
            portfolio_context=portfolio_context
        )

        try:
            response = await self.llm_service.generate_json(prompt)
            scenarios_data = response.get("scenarios", [])

            if not scenarios_data:
                return None

            # Convert to ScenarioForecast objects
            scenarios = []
            for s in scenarios_data:
                adj_return = portfolio_return * (1 + s.get("annual_return_adjustment", 0))
                adj_vol = portfolio_volatility * (1 + s.get("volatility_adjustment", 0))

                scenarios.append(ScenarioForecast(
                    name=s.get("name", "Scenario"),
                    probability=s.get("probability", 0.33),
                    description=s.get("description", ""),
                    expected_portfolio_value=investable_amount * (1 + adj_return),
                    expected_return=adj_return,
                    annual_volatility=adj_vol,
                    trajectory=self._generate_trajectory(investable_amount, adj_return)
                ))

            return scenarios

        except Exception as e:
            self.logger.error(f"Error generating LLM scenarios: {e}")
            return None

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

    def _build_optimization_constraints(
        self,
        num_assets: int,
        tickers: List[str],
        constraints: Optional['PortfolioConstraints'] = None
    ) -> tuple:
        """
        Build optimization constraints and bounds based on user input.

        Returns:
            (constraints_list, bounds_list)
        """
        # Start with basic constraint: weights sum to 1
        constraints_list = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
        bounds_list = tuple((0.0, 1.0) for _ in range(num_assets))

        if not constraints:
            return constraints_list, bounds_list

        # Apply max asset weight constraint
        if constraints.max_asset_weight is not None:
            bounds_list = tuple((0.0, constraints.max_asset_weight) for _ in range(num_assets))

        # Handle excluded assets
        if constraints.excluded_assets:
            for i, ticker in enumerate(tickers):
                if ticker in constraints.excluded_assets:
                    bounds_list = list(bounds_list)
                    bounds_list[i] = (0.0, 0.0)  # Force 0 weight
                    bounds_list = tuple(bounds_list)

        # Apply sector constraints if we have sector mapping
        if constraints.sector_constraints and self.config_service:
            try:
                sector_map = self.config_service.get_sector_mapping()
                if sector_map:
                    for sector, limits in constraints.sector_constraints.items():
                        # Find tickers in this sector
                        sector_indices = [
                            i for i, ticker in enumerate(tickers)
                            if sector_map.get(ticker) == sector
                        ]

                        if sector_indices:
                            # Max constraint for sector
                            if 'max' in limits:
                                constraints_list.append({
                                    'type': 'ineq',
                                    'fun': lambda x, idx=sector_indices: limits['max'] - np.sum(x[idx])
                                })

                            # Min constraint for sector
                            if 'min' in limits:
                                constraints_list.append({
                                    'type': 'ineq',
                                    'fun': lambda x, idx=sector_indices: np.sum(x[idx]) - limits['min']
                                })
            except Exception as e:
                self.logger.warning(f"Could not apply sector constraints: {e}")

        # Apply max volatility constraint
        if constraints.max_volatility is not None:
            # This requires a more complex approach as it's not linear
            # For now, we'll handle it post-optimization (filter results)
            pass

        return constraints_list, bounds_list

    def _filter_small_positions(
        self,
        weights: Dict[str, float],
        min_position_size: float = 0.01
    ) -> Dict[str, float]:
        """Filter out positions below minimum size and re-normalize."""
        filtered = {k: v for k, v in weights.items() if v >= min_position_size}

        if not filtered:
            return weights

        # Re-normalize to sum to 1
        total = sum(filtered.values())
        return {k: v / total for k, v in filtered.items()}

    def _calculate_mean_variance_constrained(
        self,
        mean_returns: pd.Series,
        cov_matrix: pd.DataFrame,
        constraints: Optional['PortfolioConstraints'] = None,
        fast: bool = False
    ) -> Tuple[List[EfficientFrontierPoint], Dict[str, Any]]:
        """
        Calculate efficient frontier with user-specified constraints.

        This is the constrained version of _calculate_mean_variance that supports:
        - Max asset weight (e.g., no more than 20% in any single asset)
        - Excluded assets
        - Sector constraints (max/min per sector)
        - Minimum position size
        - Min/max holdings
        """
        num_assets = len(mean_returns)
        args = (mean_returns.values, cov_matrix.values)
        tickers = mean_returns.index.tolist()
        risk_free_rate = 0.04  # TODO: Config

        # Build constraints and bounds
        constraints_list, bounds_list = self._build_optimization_constraints(
            num_assets, tickers, constraints
        )

        def portfolio_volatility(weights, mean_returns, cov_matrix):
            return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

        def portfolio_return(weights, mean_returns, cov_matrix):
            return np.sum(mean_returns * weights)

        def neg_sharpe_ratio(weights, mean_returns, cov_matrix):
            p_ret = portfolio_return(weights, mean_returns, cov_matrix)
            p_vol = portfolio_volatility(weights, mean_returns, cov_matrix)
            return -(p_ret - risk_free_rate) / p_vol

        # 1. Max Sharpe Ratio with constraints
        result_max_sharpe = sco.minimize(
            neg_sharpe_ratio,
            num_assets * [1./num_assets],
            args=args,
            method='SLSQP',
            bounds=bounds_list,
            constraints=constraints_list
        )

        if not result_max_sharpe.success:
            self.logger.warning(f"Constrained optimization failed: {result_max_sharpe.message}")
            # Fall back to unconstrained
            return self._calculate_mean_variance(mean_returns, cov_matrix)

        # Apply min position size filter
        max_sharpe_weights = dict(zip(tickers, result_max_sharpe.x))
        if constraints:
            max_sharpe_weights = self._filter_small_positions(
                max_sharpe_weights,
                constraints.min_position_size
            )

        # Check min/max holdings constraint
        num_holdings = len(max_sharpe_weights)
        if constraints:
            if num_holdings < constraints.min_holdings:
                self.logger.warning(
                    f"Optimization only has {num_holdings} holdings, "
                    f"minimum required is {constraints.min_holdings}. "
                    "Consider relaxing constraints."
                )
            elif num_holdings > constraints.max_holdings:
                # Keep only top holdings
                sorted_items = sorted(
                    max_sharpe_weights.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
                max_sharpe_weights = dict(sorted_items[:constraints.max_holdings])
                # Re-normalize
                total = sum(max_sharpe_weights.values())
                max_sharpe_weights = {k: v / total for k, v in max_sharpe_weights.items()}

        max_sharpe_ret = portfolio_return(
            list(max_sharpe_weights.values()),
            mean_returns.values,
            cov_matrix.values
        )
        max_sharpe_vol = portfolio_volatility(
            list(max_sharpe_weights.values()),
            mean_returns.values,
            cov_matrix.values
        )

        optimal_portfolio = {
            "annual_return": max_sharpe_ret,
            "annual_volatility": max_sharpe_vol,
            "sharpe_ratio": (max_sharpe_ret - risk_free_rate) / max_sharpe_vol,
            "weights": max_sharpe_weights
        }

        # 2. Efficient Frontier with constraints
        def volatility_fun(weights, mean_returns, cov_matrix):
            return portfolio_volatility(weights, mean_returns, cov_matrix)

        result_min_vol = sco.minimize(
            volatility_fun,
            num_assets * [1./num_assets],
            args=args,
            method='SLSQP',
            bounds=bounds_list,
            constraints=constraints_list
        )

        min_ret = portfolio_return(result_min_vol.x, mean_returns.values, cov_matrix.values)
        max_ret = mean_returns.max()

        target_returns = np.linspace(min_ret, max_ret, 5 if fast else 20)
        efficient_frontier = []

        for target in target_returns:
            constraints_ef = [
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
                {'type': 'eq', 'fun': lambda x: portfolio_return(x, mean_returns.values, cov_matrix.values) - target}
            ]

            result = sco.minimize(
                volatility_fun,
                num_assets * [1./num_assets],
                args=args,
                method='SLSQP',
                bounds=bounds_list,
                constraints=constraints_ef
            )

            if result.success:
                vol = result.fun
                ret = target
                sharpe = (ret - risk_free_rate) / vol
                weights = dict(zip(tickers, result.x))

                # Apply min position filter
                if constraints:
                    weights = self._filter_small_positions(
                        weights,
                        constraints.min_position_size
                    )

                point = EfficientFrontierPoint(
                    annual_volatility=vol,
                    annual_return=ret,
                    sharpe_ratio=sharpe,
                    weights=weights
                )
                efficient_frontier.append(point)

        return efficient_frontier, optimal_portfolio

    def _calculate_mean_variance(self, mean_returns: pd.Series, cov_matrix: pd.DataFrame, fast: bool = False) -> Tuple[List[EfficientFrontierPoint], Dict[str, Any]]:
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
        
        target_returns = np.linspace(min_ret, max_ret, 5 if fast else 20)
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
        """
        Generate scenario-based forecasts for the optimal portfolio.

        Uses LLM-powered scenario generation if available, otherwise falls back
        to hardcoded scenarios.
        """
        scenarios = []

        # Try to use LLM for scenario generation if available
        if self.llm_service:
            try:
                llm_scenarios = await self._generate_llm_scenarios(
                    optimal_weights, investable_amount, valid_tickers,
                    expected_annual_returns, cov_matrix
                )
                if llm_scenarios:
                    return llm_scenarios
            except Exception as e:
                self.logger.warning(f"LLM scenario generation failed, using fallback: {e}")

        # Base case - use the expected returns as-is
        base_return = sum(optimal_weights[t] * expected_annual_returns[t] for t in valid_tickers if t in optimal_weights)
        base_variance: float = 0
        for i, t1 in enumerate(valid_tickers):
            if t1 not in optimal_weights: continue
            for j, t2 in enumerate(valid_tickers):
                if t2 not in optimal_weights: continue
                base_variance += optimal_weights[t1] * optimal_weights[t2] * cov_matrix.iloc[i, j] # type: ignore
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
    ) -> Optional[Dict[str, Any]]:
        """
        Generate an LLM-powered analysis report for the portfolio.

        Returns a dict containing:
        - report: The main analysis report
        - follow_up_suggestions: List of suggested follow-up research questions
        """
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
                    "expected_return": f"{(a.expected_return or 0) * 100:.2f}%"
                }
                for a in sorted(optimal_assets, key=lambda x: x.weight, reverse=True)[:5]
            ],
            "scenarios": [
                {
                    "name": s.name,
                    "probability": f"{s.probability * 100:.0f}%",
                    "expected_value": f"{s.expected_portfolio_value:.2f} {currency}",
                    "expected_return": f"{(s.expected_return or 0) * 100:.2f}%",
                    "volatility": f"{(s.annual_volatility or 0) * 100:.2f}%"
                }
                for s in scenarios
            ]
        }

        # Check for concentration issues to potentially suggest constraints
        max_weight = max([a.weight for a in optimal_assets]) if optimal_assets else 0
        num_holdings = len(optimal_assets)
        concentration_warning = max_weight > 0.25 or num_holdings < 5

        # Determine if we should suggest constraints
        suggest_constraints = max_weight > 0.25 or num_holdings < 5 or metrics.get('annual_volatility', 0) > 0.15

        prompt = self.prompt_manager.render_prompt(
            "portfolio_optimizer/portfolio_report.jinja",
            portfolio_summary=portfolio_summary,
            suggest_constraints=suggest_constraints
        )

        try:
            # Create tools if dependencies are available
            tools = None
            if self.forecasting_engine and self.risk_calculator and self.macro_service:
                from app.services.forecasting_tools import create_forecasting_tools
                tools = create_forecasting_tools(
                    self.forecasting_engine,
                    self.risk_calculator,
                    self.history_service,
                    self.macro_service
                )

            response = await self.llm_service.generate_json(prompt, use_cache=True, tools=tools)
            result = {
                "report": response.get("report", ""),
                "follow_up_suggestions": response.get("follow_up_suggestions", [])
            }

            # Include constraint suggestions if they exist
            if "constraint_suggestions" in response:
                result["constraint_suggestions"] = response.get("constraint_suggestions", [])
            # If LLM didn't provide them but issues exist, generate them separately
            elif suggest_constraints:
                optimal_weights = {a.ticker: a.weight for a in optimal_assets}
                constraint_suggestions = await self._generate_constraint_suggestions(
                    optimal_weights, metrics, scenarios
                )
                if constraint_suggestions:
                    result["constraint_suggestions"] = constraint_suggestions

            return result
        except Exception as e:
            self.logger.error(f"Failed to generate LLM report: {e}")
            return None

    def _calculate_backtest_performance(
        self,
        optimal_weights: Dict[str, float],
        test_data: pd.DataFrame,
        training_data: pd.DataFrame,
        initial_amount: float,
        historical_date: datetime.datetime,
        account_type: Optional[str] = None
    ):
        """
        Calculate how the optimized portfolio would have performed.

        Uses only forward-looking data (test_data) to validate the optimization.

        Args:
            optimal_weights: Portfolio weights from optimization
            test_data: Price data AFTER historical_date (forward-looking)
            training_data: Price data BEFORE historical_date (used for optimization)
            initial_amount: Initial investment amount
            historical_date: The date that splits training/test data
            account_type: Account type for tax calculations

        Returns:
            BacktestResult with trajectory and metrics
        """
        from app.models.portfolio import BacktestResult

        # Filter weights to only include tickers in test_data
        valid_weights = {k: v for k, v in optimal_weights.items() if k in test_data.columns}

        if not valid_weights:
            raise ValueError("No valid weights for backtesting")

        # Calculate daily portfolio returns
        portfolio_returns = (test_data[list(valid_weights.keys())].pct_change() * pd.Series(valid_weights)).sum(axis=1)
        portfolio_returns = portfolio_returns.dropna()

        # Calculate portfolio value over time (starting from initial_amount)
        portfolio_value = initial_amount * (1 + portfolio_returns).cumprod()

        # Calculate benchmark (60/40 SPY/AGG)
        benchmark_weights = {'SPY': 0.6, 'AGG': 0.4}
        available_benchmark = {k: v for k, v in benchmark_weights.items() if k in test_data.columns}

        if len(available_benchmark) == 2:
            # Normalize weights if both available
            total = sum(available_benchmark.values())
            available_benchmark = {k: v/total for k, v in available_benchmark.items()}

        benchmark_returns = (test_data[list(available_benchmark.keys())].pct_change() * pd.Series(available_benchmark)).sum(axis=1)
        benchmark_returns = benchmark_returns.dropna()
        benchmark_value = initial_amount * (1 + benchmark_returns).cumprod()

        # Calculate pre-tax metrics
        final_value = portfolio_value.iloc[-1]
        pre_tax_total_return = (final_value / initial_amount) - 1

        # Max drawdown
        rolling_max = portfolio_value.expanding().max()
        drawdown = (portfolio_value - rolling_max) / rolling_max
        max_drawdown = drawdown.min()

        # Recovery time (if drawdown occurred)
        recovery_date = None
        recovery_days = None
        if max_drawdown < -0.05:  # 5% or more drop
            max_dd_date = drawdown.idxmin()
            recovery_mask = portfolio_value > portfolio_value.loc[max_dd_date]
            if recovery_mask.any():
                recovery_date = portfolio_value[recovery_mask].index[0]
                recovery_days = (recovery_date - max_dd_date).days

        # Calculate additional metrics
        volatility = portfolio_returns.std() * np.sqrt(252)

        # Calculate annualized return (CAGR)
        days = len(portfolio_value)
        years = days / 252
        cagr = (final_value / initial_amount) ** (1 / years) - 1 if years > 0 else 0

        # Sharpe ratio (assume 4% risk-free rate)
        risk_free_rate = 0.04
        sharpe_ratio = (cagr - risk_free_rate) / volatility if volatility > 0 else 0

        # Calculate tax impact
        capital_gains_tax = 0.0
        tax_rate = 0.0
        after_tax_final_value = final_value

        if account_type and account_type != 'nisa_growth' and account_type != 'nisa_general' and account_type != 'isa':
            # Get tax rate from config
            tax_rate = self.config_service.get_tax_rate_for_account(account_type, holding_period_days=365)

            # Calculate capital gains tax (simplified: tax on gains at end)
            capital_gain = max(0, final_value - initial_amount)
            capital_gains_tax = capital_gain * tax_rate
            after_tax_final_value = final_value - capital_gains_tax

        after_tax_return = (after_tax_final_value / initial_amount) - 1

        # Build trajectory
        trajectory = [
            {
                'date': date.isoformat(),
                'value': float(value),
                'pre_tax_value': float(portfolio_value.iloc[i]) if i == len(portfolio_value) - 1 else float(value)
            }
            for i, (date, value) in enumerate(zip(portfolio_value.index, portfolio_value))
        ]

        # Build benchmark trajectory
        benchmark_trajectory = [
            {'date': date.isoformat(), 'value': float(value)}
            for date, value in zip(benchmark_value.index, benchmark_value)
        ]

        # Build metrics dict
        metrics = {
            'total_return': after_tax_return,
            'pre_tax_total_return': pre_tax_total_return,
            'final_value': after_tax_final_value,
            'volatility': float(volatility),
            'sharpe_ratio': float(sharpe_ratio),
            'max_drawdown': float(max_drawdown),
            'recovery_days': recovery_days,
            'cagr': float(cagr),
            'capital_gains_tax': float(capital_gains_tax) if capital_gains_tax > 0 else 0.0,
            'tax_rate': float(tax_rate),
            'tax_impact': float(capital_gains_tax / final_value) if final_value > 0 else 0.0
        }

        return BacktestResult(
            trajectory=trajectory,
            benchmark_trajectory=benchmark_trajectory,
            metrics=metrics,
            start_date=test_data.index[0].isoformat(),
            end_date=test_data.index[-1].isoformat(),
            account_type=account_type,
            capital_gains_tax=float(capital_gains_tax) if capital_gains_tax > 0 else None
        )

    async def _generate_constraint_suggestions(
        self,
        optimal_weights: Dict[str, float],
        metrics: Dict[str, float],
        scenarios: List[ScenarioForecast]
    ) -> List[Dict[str, Any]]:
        """
        Ask LLM to suggest portfolio constraints if optimization has issues.

        Detects common portfolio problems and suggests specific constraints.
        """
        import json

        issues = []
        suggestions = []

        # Check for concentration issues
        max_weight = max(optimal_weights.values()) if optimal_weights else 0
        if max_weight > 0.30:
            # Find the ticker with max weight
            max_ticker = max(optimal_weights.keys(), key=lambda k: optimal_weights[k]) if optimal_weights else "Unknown"
            issues.append(f"Highest concentration: {max_weight:.1%} in {max_ticker}")

        # Check for low diversification
        num_holdings = len(optimal_weights)
        if num_holdings < 5:
            issues.append(f"Only {num_holdings} holdings (too concentrated)")

        # Check for extreme volatility
        vol = metrics.get('annual_volatility', 0)
        if vol > 0.20:
            issues.append(f"High volatility: {vol:.1%}")

        # If issues found and LLM available, generate suggestions
        if issues and self.llm_service:
            prompt = self.prompt_manager.render_prompt(
                "portfolio_optimizer/constraint_suggestions.jinja",
                issues_data={"issues": issues},
                optimal_weights=optimal_weights,
                expected_annual_return=f"{metrics.get('expected_annual_return', 0) * 100:.1f}%",
                annual_volatility=f"{metrics.get('annual_volatility', 0) * 100:.1f}%",
                num_holdings=num_holdings
            )

            try:
                response = await self.llm_service.generate_json(prompt, use_cache=False)
                suggestions = response.get("constraint_suggestions", [])

                # Add metadata
                for s in suggestions:
                    s['generated_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                    s['source'] = 'llm_analysis'

                self.logger.info(f"Generated {len(suggestions)} constraint suggestions")
                return suggestions

            except Exception as e:
                self.logger.error(f"Failed to generate constraint suggestions: {e}")
        else:
            self.logger.info("No optimization issues detected, no constraints needed")

        return suggestions
