from typing import List, Dict, Any, Optional
import yaml
from pathlib import Path
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


class ConfigService:
    def __init__(self, config_path: str|None = None):
        # Default to backend/config/etf_config.yaml
        self.config_path = Path(__file__).parent.parent.parent / "config" / "etf_config.yaml" if config_path is None else Path(config_path)
        self._config = None

    def _load_config(self) -> Dict[str, Any]:
        """Load YAML config file."""
        if self._config is None:
            with open(self.config_path, 'r') as f:
                self._config = yaml.safe_load(f)
        return self._config

    def get_all_etfs(self) -> List[ETFConfig]:
        """Get all ETF configurations."""
        config = self._load_config()
        return [ETFConfig(**etf) for etf in config['etfs']]

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
        config = self._load_config()
        return config.get('data_settings', {})

    def get_fundamental_fields(self) -> List[str]:
        """Get list of fundamental fields to fetch."""
        config = self._load_config()
        return config.get('fundamental_fields', [])

    def get_commission_settings(self) -> Dict[str, Any]:
        """Get commission settings."""
        config = self._load_config()
        return config.get('commission_settings', {
            "type": "flat_per_trade",
            "value": 0.0,
            "min_commission": 0.0,
            "currency": "USD"
        })
