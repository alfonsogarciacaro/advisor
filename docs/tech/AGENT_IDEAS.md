# Future LangGraph Agents Ideas

This document outlines potential AI agents that could be implemented using LangGraph in the Advisor application. These are designed for the target investor profile: **family-focused, long-term, low-risk, retirement planning with passive investment strategy**.

## Priority Agents (High Value for Target Profile)

### 1. Stress Testing Agent

**Purpose**: Run "what-if" scenarios on existing portfolios to understand potential risks

**Use Cases**:
- User asks: "What happens to my portfolio if there's a 2008-style recession?"
- User asks: "How would my portfolio perform if tech drops 30%?"
- User asks: "Impact of Fed raising rates by 2%?"

**Workflow**:
```
1. Parse stressor event from natural language
2. Use LLM to determine scenario parameters (drift, volatility adjustments)
3. Fetch user's current portfolio allocation
4. Run Monte Carlo simulations using ForecastingEngine
5. Calculate portfolio-level metrics under stress scenario
6. Generate visualizations ( projected values, drawdowns)
7. LLM explains results in plain language with actionable insights
```

**Integration Points**:
- ForecastingEngine (for simulations)
- LLMService (for scenario generation and explanation)
- PortfolioOptimizer (to read portfolio allocation)

**User Value**: Helps long-term investors understand tail risks and make informed decisions

---

### 2. Rebalancing Assistant Agent

**Purpose**: Monitor portfolio drift and recommend optimal rebalancing actions

**Use Cases**:
- User asks: "Does my portfolio need rebalancing?"
- User asks: "How should I rebalance with minimal taxes?"
- Automated: "Alert me when any asset drifts >5% from target"

**Workflow**:
```
1. Fetch current holdings vs target allocation
2. Calculate drift percentages for each asset
3. Fetch current prices and transaction costs
4. Analyze tax implications (NISA lots, ordinary accounts)
5. Optimize rebalancing to minimize costs and taxes
6. Generate actionable trade list with specific quantities
7. LLM explains rationale and priority
```

**Integration Points**:
- HistoryService (current prices)
- ConfigService (commission settings, tax rules)
- LLMService (recommendation generation)

**User Value**: Automates portfolio maintenance, minimizes transaction costs and taxes

---

### 3. Tax Optimization Agent

**Purpose**: Optimize asset placement across different account types (taxable, NISA, iDeCo, etc.)

**Use Cases**:
- User asks: "Which assets should I put in my NISA account?"
- User asks: "How do I minimize taxes on my portfolio?"
- User asks: "Should I prioritize iDeCo or taxable investing?"

**Workflow**:
```
1. Fetch user's account types and balances (configurable)
2. Fetch tax rules for each account type (NISA, iDeCo, taxable)
3. Analyze asset characteristics (dividend yield, capital gains potential)
4. Optimize asset placement across accounts
5. Calculate tax savings vs suboptimal placement
6. Generate recommendations with tax impact projections
7. LLM explains strategy in plain language
```

**Integration Points**:
- ConfigService (tax rules, account types)
- PortfolioOptimizer (allocation optimization)
- LLMService (explanation generation)

**User Value**: Maximizes after-tax returns, critical for long-term wealth building

---

### 4. Recurring Investment (DCA) Agent

**Purpose**: Optimize dollar-cost averaging strategies for regular investors

**Use Cases**:
- User asks: "How should I invest my monthly ¥50,000?"
- User asks: "Should I vary my DCA amounts based on market conditions?"
- User asks: "What's the optimal schedule for my biweekly investment?"

**Workflow**:
```
1. Fetch user's target allocation and investment schedule
2. Fetch current portfolio and recent contributions
3. Check if any assets are underweight relative to target
4. Calculate optimal split for next investment
5. Consider transaction costs (avoid tiny trades)
6. Consider tax account space availability
7. Generate investment schedule with specific allocations
8. LLM explains strategy and answers questions
```

**Integration Points**:
- PortfolioOptimizer (target allocation)
- HistoryService (current holdings)
- ConfigService (commission, account types)

**User Value**: Automates regular investing, maintains allocation, reduces decision fatigue

---

### 5. Risk Diagnostic Agent

**Purpose**: Explain portfolio risks in plain language for non-expert investors

**Use Cases**:
- User asks: "What are the biggest risks to my portfolio?"
- User asks: "Is my portfolio too concentrated?"
- User asks: "How sensitive is my portfolio to interest rate changes?"

**Workflow**:
```
1. Calculate comprehensive risk metrics:
   - VaR, CVaR (tail risk)
   - Beta, R-squared (market sensitivity)
   - Sector/geographic concentrations
   - Correlation analysis
   - Drawdown history
2. Identify top risk factors
3. Compare to benchmarks and risk tolerance
4. Check correlation with income sources (job, etc.)
5. LLM generates narrative explanation with evidence
6. Suggest mitigation strategies if needed
```

**Integration Points**:
- RiskCalculator (risk metrics)
- HistoryService (correlations)
- MacroService (regime detection)
- LLMService (explanation)

**User Value**: Helps passive investors understand and control risk exposure

---

### 6. Dividend Strategy Agent

**Purpose**: Optimize portfolio for income generation during retirement

**Use Cases**:
- User asks: "How can I generate ¥500k/month in dividends?"
- User asks: "Should I focus on high-dividend or growth ETFs?"
- User asks: "Which dividend ETFs have the safest payouts?"

**Workflow**:
```
1. Fetch user's income requirements and timeline
2. Screen ETFs by dividend yield, payout ratio, history
3. Analyze dividend sustainability metrics
4. Optimize portfolio for income vs growth balance
5. Project monthly/annual dividend stream
6. Assess tax implications of dividend income
7. Generate portfolio with dividend forecast
8. LLM explains strategy and risks
```

**Integration Points**:
- HistoryService (dividend history)
- PortfolioOptimizer (income-focused optimization)
- LLMService (analysis)

**User Value**: Supports retirement planning with predictable income

---

### 7. Market Regime Monitor Agent

**Purpose**: Detect and explain current market conditions in simple terms

**Use Cases**:
- User asks: "Is now a good time to invest?"
- User asks: "What's happening in the market?"
- Automated: "Alert me if market enters bear territory"

**Workflow**:
```
1. Fetch recent market data (SPY, VIX, etc.)
2. Calculate technical indicators (RSI, MACD, moving averages)
3. Determine regime (bull/bear/neutral, volatile/calm)
4. Fetch macro indicators (interest rates, yield curve)
5. LLM synthesizes into plain-language explanation
6. Provide historical context
7. Suggest portfolio adjustments if significant change
```

**Integration Points**:
- HistoryService (market data)
- MacroService (macro indicators)
- LLMService (explanation)

**User Value**: Keeps passive investors informed without overwhelming them

---

### 8. Goal-Based Planning Agent

**Purpose**: Map investment strategies to life goals (retirement, education, etc.)

**Use Cases**:
- User asks: "Can I retire at 60 with my current savings?"
- User asks: "How much should I save for my child's education?"
- User asks: "Will I have enough for a house down payment in 5 years?"

**Workflow**:
```
1. Parse goal and timeline from user input
2. Fetch current portfolio and savings rate
3. Project future value using Monte Carlo
4. Calculate probability of achieving goal
5. Suggest adjustments (higher savings, different allocation)
6. Run scenarios (what if markets perform poorly?)
7. Generate actionable plan with milestones
8. LLM explains in encouraging, practical terms
```

**Integration Points**:
- ForecastingEngine (projections)
- PortfolioOptimizer (allocation suggestions)
- LLMService (plan generation)

**User Value**: Connects investing to real-life objectives, motivates saving

---

## Implementation Considerations

### Shared Infrastructure Needs

1. **User Context Persistence**: All agents need access to:
   - Current portfolio holdings
   - Risk tolerance preferences
   - Tax account configuration
   - Life goals and timeline
   - Recurring investment settings

2. **Tool Integration**: Most agents will use:
   - ForecastingEngine (simulations)
   - HistoryService (market data)
   - LLMService (reasoning)
   - RiskCalculator (metrics)
   - ConfigService (taxes, costs)

3. **UI Patterns**:
   - Quick action buttons for common queries
   - Natural language input for custom questions
   - Follow-up suggestions after each interaction
   - Deep-dive buttons on metrics
   - Save conversations to plan history

### Priority Order (Recommended)

1. **Stress Testing Agent** - High value, relatively simple, uses existing infrastructure
2. **Rebalancing Assistant** - Practical need for long-term investors
3. **Tax Optimization Agent** - Critical for Japanese investors (NISA/iDeCo)
4. **DCA Agent** - Automates regular investing
5. **Risk Diagnostic** - Educational and practical
6. **Dividend Strategy** - Retirement planning focus
7. **Market Regime Monitor** - Nice-to-have awareness
8. **Goal-Based Planning** - Most complex, highest value

---

## Notes

- All agents should respect the target user profile: passive, long-term, low-risk
- Avoid recommending active trading, market timing, or complex derivatives
- Focus on education and empowerment, not speculation
- Always provide context and explain recommendations
- Consider Japanese market specifics (NISA, iDeCo, Japanese ETFs)
