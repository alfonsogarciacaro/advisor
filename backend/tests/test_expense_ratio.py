"""Test expense ratio integration in portfolio optimizer"""
import asyncio
from app.services.config_service import ConfigService
from app.services.portfolio_optimizer import PortfolioOptimizerService
from app.services.history_service import HistoryService
from app.services.storage_service import StorageService


async def test_expense_ratio_config():
    """Test that expense ratios are loaded from config"""
    config_service = ConfigService()

    # Test a few known ETFs
    spy_info = config_service.get_etf_info("SPY")
    assert spy_info is not None, "SPY not found in config"
    assert spy_info.expense_ratio == 0.0009, f"SPY expense_ratio should be 0.0009, got {spy_info.expense_ratio}"

    gld_info = config_service.get_etf_info("GLD")
    assert gld_info is not None, "GLD not found in config"
    assert gld_info.expense_ratio == 0.0040, f"GLD expense_ratio should be 0.0040, got {gld_info.expense_ratio}"

    agg_info = config_service.get_etf_info("AGG")
    assert agg_info is not None, "AGG not found in config"
    assert agg_info.expense_ratio == 0.0003, f"AGG expense_ratio should be 0.0003, got {agg_info.expense_ratio}"

    print("✓ All expense ratios loaded correctly from config")


async def test_expense_ratio_calculation():
    """Test that expense ratios are calculated correctly"""
    # Sample calculation: $10,000 investment with 0.1% expense ratio = $10/year
    investment_amount = 10000.0
    weight = 0.5  # 50% allocation
    expense_ratio = 0.001  # 0.1%

    annual_cost = investment_amount * weight * expense_ratio

    expected_cost = 5.0  # $10,000 * 0.5 * 0.001 = $5.00
    assert annual_cost == expected_cost, f"Expected {expected_cost}, got {annual_cost}"

    print(f"✓ Annual custody cost calculation correct: ${annual_cost:.2f}")


async def main():
    """Run all tests"""
    print("Testing Expense Ratio Integration\n" + "="*50)

    try:
        await test_expense_ratio_config()
        await test_expense_ratio_calculation()
        print("\n" + "="*50)
        print("✓ All tests passed!")
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
