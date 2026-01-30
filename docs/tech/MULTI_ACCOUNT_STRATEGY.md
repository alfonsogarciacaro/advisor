# Multi-Account Investment Strategy

## Overview

A single investment plan can contain **multiple tax-advantaged accounts** to optimize tax efficiency across different account types and their respective limits.

## Supported Account Types (Japan-focused)

| Account Type | Annual Limit | Tax Benefits | Description |
|--------------|--------------|--------------|-------------|
| **NISA General** | ¥1.2M | 0% dividend + capital gains | Broad market investments |
| **NISA Growth** | ¥1.8M | 0% dividend + capital gains | High-growth investments |
| **iDeCo** | ¥144K-¥816K* | 0% taxes + contribution deduction | Private pension |
| **Taxable** | Unlimited | Standard 20.315% tax | No restrictions |

*iDeCo limit varies by occupation and age

## Example: Multi-Account Strategy

### Scenario: Investing ¥3M/year with optimal tax placement

```
Plan: "Retirement Portfolio - Age 40"

Accounts:
┌─────────────────┬──────────────┬─────────────┬──────────────┐
│ Account         │ Allocation   │ Tax Savings │ Asset Type   │
├─────────────────┼──────────────┼─────────────┼──────────────┤
│ NISA Growth     │ ¥1,800,000   │ ~¥270K/yr   │ Growth ETFs  │
│ NISA General    │ ¥1,200,000   │ ~¥180K/yr   │ Dividend ETFs│
│ Taxable         │ ¥0           │ -           │ -            │
└─────────────────┴──────────────┴─────────────┴──────────────┘

Total: ¥3,000,000/year
Annual Tax Savings: ~¥450,000
```

## Data Model Support

### Plan Structure

```typescript
interface Plan {
    plan_id: string;
    name: string;

    // Multiple accounts supported
    tax_accounts: TaxAccount[];  // ← List of accounts

    // Global optimization settings
    risk_preference: RiskProfile;
    recurring_investment: RecurringInvestment;

    // Optimization result handles allocation across accounts
    optimization_result: OptimizationResult;
}
```

### Account Configuration

```typescript
interface TaxAccount {
    account_type: 'nisa_general' | 'nisa_growth' | 'ideco' | 'taxable';
    name: string;                    // User-defined name
    annual_limit: number;            // Max contribution per year
    current_balance: number;         // Current holdings
    available_space: number;         // Remaining space this year

    // Tax configuration
    dividend_tax_rate: number;       // 0% for NISA/iDeCo
    capital_gains_tax_rate: number;  // 0% for NISA/iDeCo
    contribution_deductible: boolean; // True for iDeCo
}
```

## Implementation Plan

### Phase 1: Account Management UI (Future)
- Add/Edit/Delete accounts within a plan
- Set annual limits for each account
- Track available space vs used space
- Visual indicators for account utilization

### Phase 2: Tax-Aware Optimization (Future)
- Prioritize tax-efficient assets in taxable accounts
- Place high-dividend assets in NISA (0% dividend tax)
- Place high-growth assets in NISA Growth (0% capital gains)
- Use iDeCo for maximum tax deduction

### Phase 3: Multi-Account DCA (Future)
- Configure different DCA amounts per account
- Respect account limits automatically
- Overflow to taxable account when NISA full

## Example: Creating a Multi-Account Plan

```typescript
const plan = await createPlan({
    name: "Tax-Optimized Retirement Portfolio",
    risk_preference: "moderate",
    user_id: "default"
});

// Later, add accounts via updatePlan()
await updatePlan(planId, {
    tax_accounts: [
        {
            account_type: "nisa_growth",
            name: "NISA Growth - High Growth",
            annual_limit: 1800000,  // ¥1.8M
            current_balance: 0,
            available_space: 1800000,
            dividend_tax_rate: 0.0,
            capital_gains_tax_rate: 0.0,
            contribution_deductible: false
        },
        {
            account_type: "nisa_general",
            name: "NISA General - Steady Growth",
            annual_limit: 1200000,  // ¥1.2M
            current_balance: 0,
            available_space: 1200000,
            dividend_tax_rate: 0.0,
            capital_gains_tax_rate: 0.0,
            contribution_deductible: false
        },
        {
            account_type: "taxable",
            name: "Taxable Account - Overflow",
            annual_limit: null,
            current_balance: 0,
            available_space: Infinity,
            dividend_tax_rate: 0.20315,
            capital_gains_tax_rate: 0.20315,
            contribution_deductible: false
        }
    ]
});
```

## DCA Configuration (Multi-Account)

```typescript
await updatePlan(planId, {
    recurring_investment: {
        enabled: true,
        frequency: "monthly",
        amount: 250000,  // ¥250K/month = ¥3M/year

        // DCA split across accounts:
        // - NISA Growth: ¥150K/month (¥1.8M/year)
        // - NISA General: ¥100K/month (¥1.2M/year)
        // - Taxable: ¥0 (fully within NISA limits)

        dividend_reinvestment: true
    }
});
```

## Tax Savings Calculation

### Without NISA (All Taxable)
- Investment: ¥3M
- Expected return: 8%
- Capital gains tax: 20.315%
- **After-tax return: 6.37%**

### With NISA Optimization
- ¥1.8M in NISA Growth @ 10% → **0% tax**
- ¥1.2M in NISA General @ 6% → **0% tax**
- **Weighted after-tax return: 8%**

**Annual benefit: ~¥500K on ¥3M investment**

## Current Status

✅ **Data Model**: Fully supports multiple accounts
✅ **API**: `TaxAccount` list in Plan model
✅ **Backend**: Plan service handles account arrays
🔄 **Frontend UI**: Account management interface (future)
🔄 **Optimization**: Tax-aware allocation logic (future)

## Next Steps

1. **Frontend UI**: Build account management interface
2. **Optimization**: Implement tax-aware allocation
3. **DCA**: Multi-account recurring investment logic
4. **Reporting**: Tax savings visualization

---

## References

- [NISA Guide (Japan)](https://www.fsa.go.jp/policy/nisa/nisa_gaido.html)
- [iDeCo Guide (Japan)](https://www.npfa.go.jp/ideco/)
- TAX ACCOUNT TYPES IN `/backend/app/models/plan.py`
