from typing import List, Dict, Any, Optional
import yaml
import asyncio
from pathlib import Path
from dataclasses import dataclass
from app.services.storage_service import StorageService
from dataclasses import dataclass


@dataclass
class ETFConfig:
    symbol: str
    name: str
    description: str
    asset_class: str
    market: str
    benchmark: Optional[str] = None
    sub_type: Optional[str] = None
    commodity: Optional[str] = None
    expense_ratio: Optional[float] = None


class ConfigService:
    def __init__(self, storage_service: Optional[StorageService] = None, config_path: str|None = None):
        # Default to backend/config/etf_config.yaml
        self.config_dir = Path(__file__).parent.parent.parent / "config"
        self.etf_config_path = self.config_dir / "etf_config.yaml"
        self.forecasting_config_path = self.config_dir / "forecasting_config.yaml"
        
        if config_path:
            self.etf_config_path = Path(config_path)

        self.storage = storage_service
        self._etf_config = None
        self._forecasting_config = None
        self._initialized = False

    async def initialize(self):
        """Initialize configuration from Storage, falling back to YAML if empty."""
        if self._initialized:
            return

        # Load YAMLs first (as fallback or seed)
        etf_yaml = self._load_yaml(self.etf_config_path)
        forecasting_yaml = self._load_yaml(self.forecasting_config_path)
        
        if self.storage:
            # Try to load from Storage
            stored_etf = await self.storage.get("config", "etfs")
            stored_forecasting = await self.storage.get("config", "forecasting")

            if stored_etf:
                self._etf_config = stored_etf
                print("Loaded ETF config from Storage")
            else:
                self._etf_config = etf_yaml
                await self.storage.save("config", "etfs", etf_yaml)
                print("Seeded ETF config to Storage from YAML")

            if stored_forecasting:
                self._forecasting_config = stored_forecasting
                print("Loaded Forecasting config from Storage")
            else:
                self._forecasting_config = forecasting_yaml
                await self.storage.save("config", "forecasting", forecasting_yaml)
                print("Seeded Forecasting config to Storage from YAML")
        else:
            self._etf_config = etf_yaml
            self._forecasting_config = forecasting_yaml
            print("ConfigService running in YAML-only mode (No Storage)")
        
        self._initialized = True

    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        """Load YAML config file."""
        if not path.exists():
            return {}
        with open(path, 'r') as f:
            content = yaml.safe_load(f)
            return content if content is not None else {}

    def _get_etf_config(self) -> Dict[str, Any]:
        if not self._initialized:
             # Fallback for sync usage before init (e.g. tests or scripts)
             return self._load_yaml(self.etf_config_path)
        return self._etf_config or {}

    def _get_forecasting_config(self) -> Dict[str, Any]:
        if not self._initialized:
             return self._load_yaml(self.forecasting_config_path)
        return self._forecasting_config or {}

    async def update_etf_config(self, new_config: Dict[str, Any]):
        """Update ETF config and persist to storage."""
        self._etf_config = new_config
        if self.storage:
            await self.storage.update("config", "etfs", new_config)

    async def update_forecasting_config(self, new_config: Dict[str, Any]):
        """Update Forecasting config and persist to storage."""
        self._forecasting_config = new_config
        if self.storage:
            await self.storage.update("config", "forecasting", new_config)

    async def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration (ETFs, forecasting, strategies)."""
        return {
            "etfs": self._get_etf_config(),
            "forecasting": self._get_forecasting_config()
        }

    async def reset_to_defaults(self):
        """Reset all configuration to YAML defaults."""
        # Reload from YAML files
        etf_yaml = self._load_yaml(self.etf_config_path)
        forecasting_yaml = self._load_yaml(self.forecasting_config_path)
        
        # Update in-memory config
        self._etf_config = etf_yaml
        self._forecasting_config = forecasting_yaml
        
        # Persist to storage
        if self.storage:
            await self.storage.update("config", "etfs", etf_yaml)
            await self.storage.update("config", "forecasting", forecasting_yaml)



    def get_all_etfs(self) -> List[ETFConfig]:
        """Get all ETF configurations."""
        try:
            config = self._get_etf_config()
            if not config or not isinstance(config, dict):
                return []
            etfs_list = config.get('etfs', [])
            if not etfs_list:
                return []
            return [ETFConfig(**etf) for etf in etfs_list]
        except Exception as e:
            # Log error but return empty list to avoid breaking the app
            import logging
            logging.warning(f"Error loading ETF configs: {e}")
            return []

    def get_all_symbols(self) -> List[str]:
        """Get all ETF symbols."""
        return [etf.symbol for etf in self.get_all_etfs()]

    def get_etfs_by_asset_class(self, asset_class: str) -> List[ETFConfig]:
        """Get ETFs filtered by asset class."""
        return [etf for etf in self.get_all_etfs() if etf.asset_class == asset_class]

    def get_etfs_by_market(self, market: str) -> List[ETFConfig]:
        """Get ETFs filtered by market (US, JP)."""
        return [etf for etf in self.get_all_etfs() if etf.market == market]

    def get_etf_info(self, symbol: str) -> Optional[ETFConfig]:
        """Get info for a specific ETF symbol."""
        for etf in self.get_all_etfs():
            if etf.symbol == symbol:
                return etf
        return None

    def get_data_settings(self) -> Dict[str, Any]:
        """Get data fetching settings."""
        config = self._get_etf_config()
        return config.get('data_settings', {})

    def get_fundamental_fields(self) -> List[str]:
        """Get list of fundamental fields to fetch."""
        config = self._get_etf_config()
        return config.get('fundamental_fields', [])

    def get_commission_settings(self) -> Dict[str, Any]:
        """Get commission settings."""
        config = self._get_etf_config()
        return config.get('commission_settings', {
            "type": "flat_per_trade",
            "value": 0.0,
            "min_commission": 0.0,
            "currency": "USD"
        })

    def get_tax_settings(self) -> Dict[str, Any]:
        """Get tax settings for backtesting and optimization."""
        # Load from strategies_config.yaml
        strategies_config_path = self.config_dir / "strategies_config.yaml"
        try:
            with open(strategies_config_path, 'r') as f:
                strategies_config = yaml.safe_load(f)
                return strategies_config.get('tax_settings', {
                    "short_term_capital_gains_rate": 0.35,
                    "long_term_capital_gains_rate": 0.15,
                    "account_types": {}
                })
        except FileNotFoundError:
            return {
                "short_term_capital_gains_rate": 0.35,
                "long_term_capital_gains_rate": 0.15,
                "account_types": {}
            }

    def get_tax_rate_for_account(self, account_type: str, holding_period_days: int = 365) -> float:
        """
        Get applicable tax rate for account type and holding period.

        Args:
            account_type: 'taxable', 'nisa_growth', 'nisa_general', 'ideco', etc.
            holding_period_days: Days held (defaults to 1 year for long-term)

        Returns:
            Tax rate (e.g., 0.15 for 15%)
        """
        tax_settings = self.get_tax_settings()

        # Get account-specific rates
        if account_type in tax_settings.get('account_types', {}):
            account_rates = tax_settings['account_types'][account_type]
            short_term_rate = account_rates.get('short_term_capital_gains_rate',
                tax_settings.get('short_term_capital_gains_rate', 0.35))
            long_term_rate = account_rates.get('long_term_capital_gains_rate',
                tax_settings.get('long_term_capital_gains_rate', 0.15))
        else:
            short_term_rate = tax_settings.get('short_term_capital_gains_rate', 0.35)
            long_term_rate = tax_settings.get('long_term_capital_gains_rate', 0.15)

        # Determine if short-term or long-term
        if holding_period_days >= 365:
            return long_term_rate
        else:
            return short_term_rate

    def get_account_limits(self) -> Dict[str, float]:
        """
        Get annual contribution limits for account types.

        Returns:
            Dict mapping account_type to annual limit (e.g., {'nisa_growth': 1800000})
        """
        tax_settings = self.get_tax_settings()
        account_types = tax_settings.get('account_types', {})

        limits = {}
        for account_type, config in account_types.items():
            # Use max_investment if available, otherwise annual_limit
            limits[account_type] = config.get('max_investment', config.get('annual_limit', 0))

        return limits

    def get_news_ttl_hours(self) -> int:
        """Get news TTL in hours (default 12h)."""
        forecasting_config = self._get_forecasting_config()
        return forecasting_config.get("cache_ttl_hours", {}).get("news", 12)
