# Playground & Historical Backtesting - User Guide

## Overview

The **Playground** feature allows you to test investment strategies using historical data to see how they would have performed in the past. This helps you:

- **Understand historical behavior** - See how strategies performed during major market events (COVID-19, 2008 financial crisis, etc.)
- **Compare account types** - Learn how taxes impact your returns (Taxable vs NISA vs iDeCo)
- **Test strategy templates** - Use pre-built investment strategies or create your own
- **Make informed decisions** - Use data to choose the right strategy for your goals

---

## Getting Started

### Accessing the Playground

1. **Create or open a plan**
   - From the plan list, click on any plan to open it
   - Or create a new plan using the "Create Plan" button

2. **Navigate to Playground**
   - In the plan detail view, click the **"Playground"** tab
   - You'll see the Historical Replay interface (the default mode)

---

## Historical Backtesting

### What is Historical Backtesting?

Historical backtesting simulates how an investment strategy would have performed if you had started investing on a specific date in the past. The system:

1. Uses only historical data **before** your start date to optimize the portfolio
2. Simulates performance **after** your start date as if you had actually invested
3. Calculates realistic after-tax returns based on your account type

This prevents "look-ahead bias" - using future information that wouldn't have been available at the time.

---

## Step-by-Step: Running Your First Backtest

### Step 1: Choose a Historical Period

You have two options:

**Option A: Quick-Select Preset Periods**

Click any preset button to test a specific historical period:

| Preset | Date | What It Tests |
|--------|------|---------------|
| 🦠 Pre-COVID | Jan 2020 | COVID-19 market crash and recovery |
| 📉 Pre-2008 Crisis | Jan 2008 | Global financial crisis |
| 💉 Post-COVID Recovery | Jan 2022 | Inflation and rate hike period |
| 📅 5 Years Ago | 5 years back | Medium-term performance |
| 📅 10 Years Ago | 10 years back | Long-term performance |

**Option B: Custom Date**

1. Click the date picker input
2. Select any past date (e.g., your birthday, a significant market event, etc.)
3. The system will use data from before that date to optimize your portfolio

---

### Step 2: Set Your Investment Amount

Enter how much you would have invested on that date:

```
Investment Amount: $10,000
```

**Tips:**
- Try different amounts to see how results scale
- Consider your actual investment capacity
- The system uses USD by default

---

### Step 3: Select an Account Type (Optional but Important!)

Choose the type of account you would use:

| Account Type | Tax Rate | When to Use |
|--------------|----------|-------------|
| 💵 Taxable | 20.315% | Regular brokerage account |
| 🆓 NISA Growth | 0% | Long-term growth investing (¥1.2M/year limit) |
| 🆓 NISA General | 0% | Balanced investing (¥3.6M/year limit) |
| 🏛️ iDeCo | 0% | Retirement savings (tax-deferred) |

**Why This Matters:**

The difference is **huge**! For example:
- **$10,000** invested in **2020** with **20% tax**: Could end up with **$11,500** after tax
- **$10,000** invested in **2020** with **0% tax** (NISA): Could end up with **$12,000**

That's **$500+** in savings just by choosing the right account!

---

### Step 4: Choose a Strategy Template (Optional)

Strategy templates are pre-built investment approaches with specific constraints:

**Conservative Income** 🛡️
- Low volatility, steady dividends
- 60%+ bonds, 40% max equities
- Best for: Retirees, risk-averse investors

**Balanced Diversifier** ⚖️
- 60/40 stock/bond mix
- 10+ holdings for diversification
- Best for: Most investors

**Aggressive Growth** 📈
- 90%+ equities, concentrated positions
- Higher volatility, higher returns
- Best for: Young investors, high risk tolerance

**Tech Heavy** 💻
- 50%+ technology sector
- High growth potential
- Best for: Tech believers

**Or select "Custom Constraints (None)"** to let the optimizer decide freely.

---

### Step 5: Run the Backtest

Click the **"▶️ Run Backtest"** button and wait!

The system will:
1. Optimize your portfolio using only data **before** your start date
2. Simulate performance through today
3. Calculate taxes based on your account type
4. Show detailed results (usually takes 30-60 seconds)

---

## Understanding Your Results

### Key Metrics Explained

#### Final Value
- **What it is**: Your portfolio value today (after taxes)
- **Example**: $12,000 (you gained $2,000)

#### Total Return
- **What it is**: Percentage gain/loss on your investment
- **Example**: +20% (your portfolio grew by 20%)

#### Max Drawdown (Worst Case)
- **What it is**: The biggest peak-to-valley drop
- **Example**: -15% (at one point, your portfolio dropped 15% from its peak)
- **Why it matters**: Helps you understand risk - can you stomach a 15% drop?

#### Recovery Time
- **What it is**: How long it took to recover from the worst drop
- **Example**: 180 days (6 months to get back to even)
- **Why it matters**: Tests your emotional resilience - would you have panicked?

#### CAGR (Compound Annual Growth Rate)
- **What it is**: Annualized return percentage
- **Example**: 8.5% per year
- **Why it matters**: Allows comparison across different time periods

#### Sharpe Ratio
- **What it is**: Risk-adjusted return (higher is better)
- **Example**: 0.85
- **Why it matters**: Did you get enough return for the risk you took?

---

### Portfolio vs Benchmark Chart

The chart shows two lines:

- **Blue line (Your Portfolio)**: Performance of your optimized strategy
- **Gray dashed line (Benchmark)**: Performance of a simple 60/40 stock/bond mix

**What to look for:**
- Did your portfolio beat the benchmark?
- How did it perform during crises?
- Was the volatility worth the extra return?

---

### Historical Event Markers

Key events that affected your portfolio are shown as badges:

- 🦠 **COVID Declared** (Mar 2020) - Market crash begins
- 📉 **Market Bottom** (Mar 2020) - S&P 500 hits bottom
- 💥 **Ukraine War** (Feb 2022) - Geopolitical risk spikes
- 📈 **Fed Rate Hikes** (Mar 2022) - Interest rates start rising

These help explain **why** your portfolio performed the way it did.

---

### Tax Impact Alert

If you used a Taxable account, you'll see a warning:

```
⚠️ Tax Impact Applied
20.315% capital gains tax applied
Consider tax-advantaged accounts (NISA/iDeCo) for better after-tax returns
```

If you used NISA/iDeCo, you'll see:

```
✅ Tax-Advantaged Account Selected
Using NISA Growth account with 0% tax rate
This could save you thousands compared to a taxable account
```

---

## Educational Insights

At the bottom of your results, you'll see a plain-language explanation:

```
If you invested on January 1, 2020, you would have gained 20% by today.
The worst drop was 15%.
It took 6 months to recover from the worst drop.
This strategy would have grown your wealth over this period.
```

This helps you understand:
1. **Real-world impact**: "If I had invested $10,000, I'd have $12,000 today"
2. **Risk tolerance**: "Could I handle a 15% drop without selling?"
3. **Time horizon**: "Would I have waited 6 months to recover?"

---

## Tips for Getting the Most Out of the Playground

### 1. Test Multiple Periods

Don't just test one period! Try:
- **Bull markets** (e.g., 2019-2021)
- **Bear markets** (e.g., 2008, early 2020)
- **Volatile periods** (e.g., 2022 with rate hikes)
- **Long periods** (5-10 years to see cycles)

### 2. Compare Account Types

Run the same backtest with different account types:

```
Same strategy, different accounts:
- Taxable: $11,500 (after paying $500 in taxes)
- NISA Growth: $12,000 (no taxes!)

That's $500 more just by using the right account!
```

### 3. Try Different Strategies

Test strategy templates side-by-side:

```
Conservative (2020-2024):
- Return: +35%
- Max Drop: -12%
- Best for: Sleep well at night

Aggressive (2020-2024):
- Return: +85%
- Max Drop: -35%
- Best for: Young investors with time to recover
```

### 4. Consider Your Time Horizon

If you're retiring in 5 years, test 5-year periods. If you're investing for 20 years, test 10+ year periods. Longer periods smooth out short-term volatility.

### 5. Don't Chase Recent Performance

Just because a strategy did amazing in 2020-2021 doesn't mean it will continue. Test across different market cycles to see consistent behavior.

---

## Common Questions

### Q: How far back can I test?

**A:** You can test back to approximately 2006 (when our ETF data begins). The further back, the more market cycles your test will include.

### Q: Why is there a "Future Simulation" mode that's disabled?

**A:** Future Simulation is coming soon! It will let you stress-test strategies with hypothetical scenarios (e.g., "What if tech drops 30%?"). For now, focus on Historical Replay.

### Q: Can I trust historical results?

**A:** Yes, but with caveats:
- ✅ The system prevents look-ahead bias (no future data)
- ✅ Taxes are calculated realistically
- ⚠️ Past performance doesn't guarantee future results
- ⚠️ The system assumes you followed the strategy perfectly (no emotion, no changes)

### Q: Should I always choose the strategy with the highest return?

**A:** Not necessarily! Consider:
- **Your risk tolerance**: Can you sleep with a 30% drop?
- **Your time horizon**: Do you have 10+ years to recover?
- **Your goals**: Are you preserving wealth or growing it?
- **Taxes**: Use NISA/iDeCo when possible to keep more of your returns

### Q: Why do some strategies show "pre-tax" and "after-tax" returns?

**A:** For taxable accounts, you pay capital gains tax when you sell. The "pre-tax" return shows what the portfolio earned, and "after-tax" shows what you actually keep. For NISA/iDeCo accounts, they're the same (0% tax).

---

## Examples

### Example 1: Conservative Investor Testing COVID-19

**Goal**: "I want to see how a conservative strategy would have done during COVID"

**Setup**:
- Period: Pre-COVID (Jan 2020)
- Amount: $10,000
- Account: NISA Growth (0% tax)
- Strategy: Conservative Income

**Results**:
- Final Value: $11,200 (+12%)
- Max Drop: -8%
- Recovery: 4 months

**Insight**: "The conservative strategy had a smaller drop and recovered quickly. I can handle this volatility."

---

### Example 2: Comparing Taxable vs NISA

**Goal**: "How much do taxes really cost me?"

**Test 1 - Taxable Account**:
- Period: 5 Years Ago
- Amount: $10,000
- Account: Taxable (20.315% tax)
- Final: $12,000 (after $600 in taxes)

**Test 2 - NISA Growth**:
- Same setup, but NISA account
- Final: $12,600 (0% tax)

**Insight**: "Using NISA would have saved me $600 in taxes. I should prioritize NISA for my investments!"

---

### Example 3: Tech-Heavy Strategy Test

**Goal**: "Should I invest mostly in tech?"

**Setup**:
- Period: 5 Years Ago
- Amount: $10,000
- Strategy: Tech Heavy
- Account: NISA Growth

**Results**:
- Final Value: $14,500 (+45%)
- Max Drop: -35%
- Recovery: 18 months

**Insight**: "Great returns, but a 35% drop that took 18 months to recover... Can I handle that emotionally? Maybe I should mix in some bonds."

---

## Next Steps

Once you've tested strategies in the Playground:

1. **Apply to Your Plan**: Use the Optimization tab to create an actual portfolio with your chosen strategy
2. **Research More**: Use the Research panel to ask questions like "Why did tech perform so well in 2023?"
3. **Monitor**: Re-run backtests periodically to see if your strategy is still working

---

## Need Help?

- **Check the docs**: Read `PLAYGROUND_IMPLEMENTATION.md` for technical details
- **Review stories**: See `USER_STORIES.md` Section 10 for all playground features
- **Ask questions**: Use the Research panel to ask specific questions about your portfolio

---

**Happy testing! 🎮** Remember: The best strategy is the one you can stick with through market ups and downs.
