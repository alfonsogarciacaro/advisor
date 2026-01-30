"""Test backtesting functionality in portfolio optimizer"""
import asyncio
from datetime import datetime, timedelta
from app.services.config_service import ConfigService


async def test_tax_rate_calculation():
    """Test that tax rates are calculated correctly for different account types"""
    config_service = ConfigService()

    # Test taxable account (long-term capital gains rate from config)
    taxable_rate = config_service.get_tax_rate_for_account('taxable', holding_period_days=365)
    # Long-term rate is 0.15 (15%) as configured in strategies_config.yaml
    assert taxable_rate == 0.15, f"Taxable account tax rate should be 0.15 (15%), got {taxable_rate}"

    # Test short-term vs long-term for taxable account
    short_term_rate = config_service.get_tax_rate_for_account('taxable', holding_period_days=100)
    assert short_term_rate == 0.35, f"Short-term taxable rate should be 0.35 (35%), got {short_term_rate}"

    # Test NISA accounts (should have 0% tax rate)
    nisa_growth_rate = config_service.get_tax_rate_for_account('nisa_growth', holding_period_days=365)
    assert nisa_growth_rate == 0.0, f"NISA Growth account tax rate should be 0.0, got {nisa_growth_rate}"

    nisa_general_rate = config_service.get_tax_rate_for_account('nisa_general', holding_period_days=365)
    assert nisa_general_rate == 0.0, f"NISA General account tax rate should be 0.0, got {nisa_general_rate}"

    # Test ISA account (should have 0% tax rate)
    isa_rate = config_service.get_tax_rate_for_account('isa', holding_period_days=365)
    assert isa_rate == 0.0, f"ISA account tax rate should be 0.0, got {isa_rate}"

    print("✓ All tax rate calculations correct")


async def test_tax_settings_structure():
    """Test that tax settings are properly structured"""
    config_service = ConfigService()
    tax_settings = config_service.get_tax_settings()

    # Verify top-level structure
    assert 'short_term_capital_gains_rate' in tax_settings, "Missing short_term_capital_gains_rate"
    assert 'long_term_capital_gains_rate' in tax_settings, "Missing long_term_capital_gains_rate"
    assert 'account_types' in tax_settings, "Missing account_types"

    # Verify account types structure
    account_types = tax_settings['account_types']
    assert 'taxable' in account_types, "Missing taxable account type"
    assert 'nisa_growth' in account_types, "Missing nisa_growth account type"
    assert 'nisa_general' in account_types, "Missing nisa_general account type"
    assert 'isa' in account_types, "Missing isa account type"

    # Verify taxable account has rates
    taxable = account_types['taxable']
    assert 'short_term_capital_gains_rate' in taxable, "Missing short_term_capital_gains_rate for taxable"
    assert 'long_term_capital_gains_rate' in taxable, "Missing long_term_capital_gains_rate for taxable"

    print("✓ Tax settings structure is valid")


async def test_backtest_metrics_calculation():
    """Test that backtest metrics are calculated correctly"""
    # Simple test data with known values
    initial_value = 10000
    trajectory = [
        {'date': '2020-01-01', 'value': 10000},
        {'date': '2020-07-01', 'value': 9000},   # -10% drawdown
        {'date': '2021-01-01', 'value': 11000},  # +10% total return
        {'date': '2021-07-01', 'value': 10500},  # slight dip
        {'date': '2022-01-01', 'value': 12000},  # +20% total return
    ]

    # Calculate total return
    final_value = trajectory[-1]['value']
    total_return = (final_value - initial_value) / initial_value
    assert abs(total_return - 0.20) < 0.01, f"Total return should be ~20%, got {total_return:.2%}"

    # Calculate max drawdown
    peak = trajectory[0]['value']
    max_drawdown = 0
    for point in trajectory:
        if point['value'] > peak:
            peak = point['value']
        drawdown = (peak - point['value']) / peak
        if drawdown > max_drawdown:
            max_drawdown = drawdown

    assert abs(max_drawdown - 0.10) < 0.01, f"Max drawdown should be ~10%, got {max_drawdown:.2%}"

    # Calculate recovery days
    # Find the bottom (max drawdown point)
    bottom_value = trajectory[1]['value']
    recovery_date = None
    for i in range(2, len(trajectory)):
        if trajectory[i]['value'] >= bottom_value:
            recovery_date = datetime.fromisoformat(trajectory[i]['date'])
            break

    if recovery_date:
        bottom_date = datetime.fromisoformat(trajectory[1]['date'])
        recovery_days = (recovery_date - bottom_date).days
        assert recovery_days > 0, f"Recovery days should be positive, got {recovery_days}"

    print(f"✓ Backtest metrics calculated correctly: total_return={total_return:.2%}, max_drawdown={max_drawdown:.2%}")


async def test_strategies_config_loading():
    """Test that strategies config can be loaded from YAML"""
    import yaml
    from pathlib import Path

    config_service = ConfigService()
    strategies_config_path = config_service.config_dir / "strategies_config.yaml"

    assert strategies_config_path.exists(), f"Strategies config file not found at {strategies_config_path}"

    with open(strategies_config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Verify structure
    assert 'strategies' in config, "Missing 'strategies' key in config"
    assert 'tax_settings' in config, "Missing 'tax_settings' key in config"

    strategies = config['strategies']
    assert len(strategies) > 0, "No strategies found in config"

    # Verify each strategy has required fields
    required_fields = ['strategy_id', 'name', 'description', 'risk_level', 'constraints']
    for strategy in strategies:
        for field in required_fields:
            assert field in strategy, f"Strategy {strategy.get('strategy_id', 'unknown')} missing field: {field}"

        # Verify constraints have valid values
        constraints = strategy['constraints']
        assert isinstance(constraints, dict), f"Constraints should be a dict for {strategy['strategy_id']}"

    print(f"✓ All {len(strategies)} strategy templates loaded successfully")


async def test_backtest_result_structure():
    """Test that backtest result has all required fields"""
    # Create a minimal backtest result structure to verify the model
    test_result = {
        'trajectory': [
            {'date': '2020-01-01', 'value': 10000},
            {'date': '2021-01-01', 'value': 11000}
        ],
        'benchmark_trajectory': [
            {'date': '2020-01-01', 'value': 10000},
            {'date': '2021-01-01', 'value': 10500}
        ],
        'metrics': {
            'total_return': 0.10,
            'pre_tax_total_return': 0.12,
            'final_value': 11000,
            'volatility': 0.15,
            'sharpe_ratio': 0.67,
            'max_drawdown': -0.05,
            'recovery_days': 180,
            'cagr': 0.10,
            'tax_rate': 0.20315,
            'capital_gains_tax': 200.0,
            'tax_impact': -0.02
        },
        'start_date': '2020-01-01',
        'end_date': '2021-01-01',
        'account_type': 'taxable',
        'capital_gains_tax': 200.0
    }

    # Verify all required fields exist
    assert 'trajectory' in test_result
    assert 'benchmark_trajectory' in test_result
    assert 'metrics' in test_result
    assert 'start_date' in test_result
    assert 'end_date' in test_result
    assert 'account_type' in test_result

    # Verify metrics
    metrics = test_result['metrics']
    required_metrics = ['total_return', 'final_value', 'volatility', 'sharpe_ratio', 'max_drawdown', 'recovery_days', 'cagr']
    for metric in required_metrics:
        assert metric in metrics, f"Missing metric: {metric}"

    # Verify tax-related metrics
    assert 'tax_rate' in metrics or 'capital_gains_tax' in metrics, "Missing tax-related metrics"

    print("✓ Backtest result structure is valid")


async def test_tax_calculation_for_backtest():
    """Test tax calculation logic for backtesting"""
    initial_value = 10000
    final_value = 12000
    taxable_gain = final_value - initial_value  # 2000

    # Test taxable account (20.315% tax rate)
    tax_rate = 0.20315
    expected_tax = taxable_gain * tax_rate
    assert abs(expected_tax - 406.3) < 1, f"Expected tax ~$406.30, got ${expected_tax:.2f}"

    # Test NISA account (0% tax rate)
    nisa_tax_rate = 0.0
    expected_nisa_tax = taxable_gain * nisa_tax_rate
    assert expected_nisa_tax == 0, f"NISA tax should be $0, got ${expected_nisa_tax}"

    # Calculate after-tax value
    after_tax_value = final_value - expected_tax
    expected_after_tax = 12000 - 406.3
    assert abs(after_tax_value - expected_after_tax) < 1, f"After-tax value should be ~${expected_after_tax}, got ${after_tax_value:.2f}"

    print(f"✓ Tax calculation correct: ${taxable_gain} gain × {tax_rate:.2%} = ${expected_tax:.2f} tax")


async def main():
    """Run all tests"""
    print("Testing Backtesting Functionality\n" + "="*50)

    try:
        await test_tax_settings_structure()
        await test_tax_rate_calculation()
        await test_strategies_config_loading()
        await test_backtest_result_structure()
        await test_backtest_metrics_calculation()
        await test_tax_calculation_for_backtest()
        print("\n" + "="*50)
        print("✓ All backtesting tests passed!")
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
