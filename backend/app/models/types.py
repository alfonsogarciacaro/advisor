"""
Shared type definitions for models.

This module contains common types used across multiple models to avoid circular imports.
"""

from enum import Enum


class RiskProfile(str, Enum):
    """Risk tolerance levels for long-term family investors"""
    VERY_CONSERVATIVE = "very_conservative"  # Max capital preservation, accept lower returns
    CONSERVATIVE = "conservative"  # Focus on stability, some growth
    MODERATE = "moderate"  # Balanced approach
    GROWTH = "growth"  # Accept higher volatility for better returns
    AGGRESSIVE = "aggressive"  # Maximum growth acceptance


class TaxAccountType(str, Enum):
    """Tax-advantaged account types, primarily for Japanese market"""
    TAXABLE = "taxable"  # Ordinary taxable account
    NISA_GENERAL = "nisa_general"  # New NISA (General Account)
    NISA_GROWTH = "nisa_growth"  # New NISA (Growth Account)
    IDECO = "ideco"  # iDeCo (Individual Defined Contribution pension)
    DC_PENSION = "dc_pension"  # Company DC pension
    OTHER = "other"  # Other country-specific accounts
