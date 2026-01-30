from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Optional, Any
from app.services.portfolio_optimizer import PortfolioOptimizerService
from app.services.history_service import HistoryService
from app.services.currency_service import CurrencyService
from app.core.dependencies import get_portfolio_optimizer_service, get_storage_service, get_logger, get_config_service, get_currency_service, get_history_service
from app.services.storage_service import StorageService
from app.services.logger_service import LoggerService
from app.services.config_service import ConfigService
from app.models.portfolio import OptimizationRequest, OptimizationResult, ValidationResult, ValidationError, PortfolioValidationRequest
from app.core.utils import sanitize_numpy

router = APIRouter()


@router.post("/optimize", response_model=Dict[str, str])
async def optimize_portfolio(
    request: OptimizationRequest,
    optimizer_service: PortfolioOptimizerService = Depends(get_portfolio_optimizer_service),
    logger: LoggerService = Depends(get_logger)
):
    """
    Trigger a portfolio optimization.
    Returns a job_id to track the progress.

    Query parameters for backtesting:
        historical_date: ISO date string for backtesting (e.g., "2020-01-01")
        use_strategy: Strategy template ID to use (e.g., "conservative_income")
        account_type: Account type for tax calculations (e.g., "taxable", "nisa_growth")
    """
    try:
        job_id = await optimizer_service.start_optimization(
            amount=request.amount,
            currency=request.currency,
            excluded_tickers=request.excluded_tickers or [],
            plan_id=request.plan_id,
            fast=request.fast or False,
            historical_date=request.historical_date,
            use_strategy_template=request.use_strategy,
            account_type=request.account_type
        )
        return {"job_id": job_id, "status": "queued"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/optimize/{job_id}", response_model=OptimizationResult)
async def get_optimization_status(
    job_id: str,
    storage_service: StorageService = Depends(get_storage_service),
    logger: LoggerService = Depends(get_logger)
):
    """
    Get the status and result of a portfolio optimization job.
    """
    job_data = await storage_service.get("optimization_jobs", job_id)
    if not job_data:
        raise HTTPException(status_code=404, detail="Job not found")

    return sanitize_numpy(job_data)


@router.delete("/optimize/cache")
async def clear_optimization_cache(
    job_id: Optional[str] = Query(None, description="Specific job ID to clear, or omit to clear all"),
    storage_service: StorageService = Depends(get_storage_service),
    logger: LoggerService = Depends(get_logger)
):
    """
    Clear cached optimization data. Either clears a specific job or all jobs.
    """
    collection = "optimization_jobs"

    if job_id:
        # Delete specific job
        await storage_service.delete(collection, job_id)
        logger.info(f"Cleared optimization cache for job {job_id}")
        return {"message": f"Cleared cache for job {job_id}", "jobs_cleared": 1}
    else:
        # Delete all jobs (this requires listing them first - implementation depends on storage service)
        # For now, return a message that this feature requires listing capability
        logger.info(f"Cache clear requested for all jobs")
        return {"message": "Clearing all jobs requires storage service list capability", "jobs_cleared": 0}


@router.post("/validate", response_model=ValidationResult)
async def validate_portfolio_holdings(
    request: PortfolioValidationRequest,
    storage_service: StorageService = Depends(get_storage_service),
    config_service: ConfigService = Depends(get_config_service),
    logger: LoggerService = Depends(get_logger)
):
    """
    Validate portfolio holdings against account limits.

    Checks that total holdings per account type do not exceed configured limits.
    All values are in the plan's base currency.
    """
    try:
        plan_id = request.plan_id
        holdings = request.holdings

        # Load plan to get base_currency
        plan_data = await storage_service.get("plans", plan_id)
        if not plan_data:
            raise HTTPException(status_code=404, detail="Plan not found")

        base_currency = plan_data.get("base_currency", "JPY")

        # Get account limits from strategies config
        account_limits = config_service.get_account_limits()

        # Sum holdings by account_type (all values already in base_currency)
        account_totals: Dict[str, float] = {}
        for holding in holdings:
            account_type = holding.account_type
            value = holding.monetary_value
            account_totals[account_type] = account_totals.get(account_type, 0) + value

        # Check limits
        errors = []
        for account_type, total in account_totals.items():
            limit = account_limits.get(account_type)
            if limit and total > limit:
                errors.append(ValidationError(
                    account_type=account_type,
                    message=f"Total holdings ({format_currency(total, base_currency)}) exceed annual limit ({format_currency(limit, base_currency)})",
                    total=total,
                    limit=limit
                ))

        valid = len(errors) == 0

        return ValidationResult(
            valid=valid,
            errors=errors,
            warnings=[]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating portfolio holdings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/etfs/available")
async def get_available_etfs(
    plan_id: str,
    storage_service: StorageService = Depends(get_storage_service),
    config_service: ConfigService = Depends(get_config_service),
    currency_service: Any = Depends(get_currency_service),
    history_service: HistoryService = Depends(get_history_service),
    logger: LoggerService = Depends(get_logger)
):
    """
    Get available ETFs with current prices in the plan's base currency.

    Returns ETF information including:
    - Current price converted to base currency
    - Eligible account types
    - Account limits with current usage
    """
    try:
        # Load plan to get base_currency
        plan_data = await storage_service.get("plans", plan_id)
        if not plan_data:
            raise HTTPException(status_code=404, detail="Plan not found")

        base_currency = plan_data.get("base_currency", "JPY")

        # Get ETF configurations
        etf_configs = config_service.get_all_etfs()
        etf_count = len(etf_configs) if etf_configs else 0
        logger.info(f"Retrieved {etf_count} ETF configs")

        if not etf_configs or etf_count == 0:
            # Return empty list if no ETFs configured
            return {
                "etfs": [],
                "account_limits": {},
                "base_currency": base_currency
            }

        # Batch fetch all prices using HistoryService (uses mock in test mode)
        symbols = [etf.symbol for etf in etf_configs]
        prices = history_service.get_latest_prices(symbols)
        logger.info(f"Fetched prices for {len(prices)} ETFs")

        # Pre-fetch FX rates we might need (avoid repeated lookups in loop)
        fx_rates = {}
        currencies_needed = set(
            CurrencyService.get_market_currency(etf.market)
            for etf in etf_configs
        )
        for curr in currencies_needed:
            if curr != base_currency:
                fx_rates[curr] = await currency_service.get_current_rate(curr, base_currency)


        # Get current prices and convert to base currency
        etfs = []
        for etf in etf_configs:
            native_price = prices.get(etf.symbol)
            if native_price is None:
                logger.warning(f"No price for {etf.symbol}")
                continue

            native_currency = CurrencyService.get_market_currency(etf.market)

            # Convert to base currency if needed
            if native_currency != base_currency:
                rate = fx_rates.get(native_currency, 1.0)
                price_base = native_price * rate
            else:
                price_base = native_price

            etfs.append({
                "symbol": etf.symbol,
                "name": etf.name,
                "eligible_accounts": ['taxable'],  # Default, can be extended in config
                "market": etf.market,
                "native_currency": native_currency,
                "current_price_base": round(price_base, 2)
            })

        # Get account limits and calculate usage
        account_limits = config_service.get_account_limits()
        account_limits_info = {}

        # Calculate current usage from plan's initial_portfolio
        initial_portfolio = plan_data.get("initial_portfolio") or []
        logger.info(f"Initial portfolio has {len(initial_portfolio)} assets")

        account_usage: Dict[str, float] = {}
        for asset in initial_portfolio:
            account_type = asset.get("account_type", "taxable")
            # Support both 'amount' (PortfolioAsset) and 'monetary_value' (AssetHolding)
            value = asset.get("monetary_value") or asset.get("amount", 0)
            account_usage[account_type] = account_usage.get(account_type, 0) + value

        logger.info(f"Account limits keys: {list(account_limits.keys()) if account_limits else 'None'}")

        if account_limits:
            for account_type, limit in account_limits.items():
                used = account_usage.get(account_type, 0)
                account_limits_info[account_type] = {
                    "annual_limit": limit,
                    "used_space": round(used, 2),
                    "available_space": round(max(0, limit - used), 2)
                }
        else:
            logger.warning("account_limits is None or empty")

        return {
            "etfs": etfs,
            "account_limits": account_limits_info,
            "base_currency": base_currency
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Error getting available ETFs: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


def format_currency(value: float, currency: str) -> str:
    """Format monetary value with currency symbol"""
    symbols = {"JPY": "¥", "USD": "$", "EUR": "€"}
    symbol = symbols.get(currency, currency)
    return f"{symbol}{value:,.0f}"
