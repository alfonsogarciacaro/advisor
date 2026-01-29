# Implementation Summary: Plan Management & Research Agent Enhancement

## Date: 2025-01-29

## Overview
This implementation adds plan management capabilities and enhances the research agent with portfolio context integration, following the requirements for a long-term, low-risk family investor profile.

## Target Investor Profile
- **Focus**: Family person, savings protection, retirement income
- **Risk**: Long-term, low-risk (configurable)
- **Time**: Passive investing, minimal market monitoring
- **Market**: Global, with Japan-specific features (NISA, iDeCo)
- **Features**: Recurring investments (DCA), dividend reinvestment

---

## Files Created

### 1. `/backend/app/models/plan.py`
New data models for plan management:

- **`RiskProfile` (Enum)**: Risk tolerance levels
  - `VERY_CONSERVATIVE`, `CONSERVATIVE`, `MODERATE`, `GROWTH`, `AGGRESSIVE`

- **`InvestmentFrequency` (Enum)**: DCA frequency options
  - `WEEKLY`, `BIWEEKLY`, `MONTHLY`, `QUARTERLY`

- **`TaxAccountType` (Enum)**: Tax-advantaged account types
  - `TAXABLE`, `NISA_GENERAL`, `NISA_GROWTH`, `IDECO`, `DC_PENSION`, `OTHER`

- **`TaxAccount`**: Configuration for tax-advantaged accounts
  - Annual limits, tax rates, withdrawal rules
  - **Multiple accounts per plan supported** (e.g., NISA + Taxable)

- **`RecurringInvestment`**: DCA configuration
  - Amount, frequency, dividend reinvestment

- **`ResearchRun`**: Research agent execution history
  - Query, results, scenarios, follow-up suggestions

- **`Plan`**: Main investment plan model
  - Portfolio allocation
  - Optimization results
  - Research history
  - **Tax configuration** (list of accounts for multi-account strategies)
  - Risk preference
  - User notes

> **Multi-Account Strategy**: Each plan can contain multiple tax-advantaged accounts (e.g., NISA Growth ¥1.8M + NISA General ¥1.2M + Taxable overflow). See `MULTI_ACCOUNT_STRATEGY.md` for details.

### 2. `/backend/app/services/plan_service.py`
Service for managing investment plans:

- **`create_plan()`**: Create new investment plan
- **`get_plan()`**: Retrieve plan by ID
- **`list_plans()`**: List all user's plans
- **`update_plan()`**: Update plan metadata
- **`attach_optimization_result()`**: Link optimization to plan
- **`add_research_run()`**: Save research agent execution
- **`delete_plan()`**: Delete a plan

### 3. `/backend/app/api/plans.py`
FastAPI routes for plan management:

- **`POST /api/plans`**: Create new plan
- **`GET /api/plans`**: List user's plans
- **`GET /api/plans/{plan_id}`**: Get specific plan
- **`PUT /api/plans/{plan_id}`**: Update plan
- **`DELETE /api/plans/{plan_id}`**: Delete plan
- **`POST /api/plans/{plan_id}/research`**: Run research agent on plan

### 4. `/docs/AGENT_IDEAS.md`
Documentation for future LangGraph agents:

Documents 8 potential future agents:
1. Stress Testing Agent
2. Rebalancing Assistant Agent
3. Tax Optimization Agent
4. Recurring Investment (DCA) Agent
5. Risk Diagnostic Agent
6. Dividend Strategy Agent
7. Market Regime Monitor Agent
8. Goal-Based Planning Agent

Each with use cases, workflows, and integration points.

---

## Files Modified

### 1. `/backend/app/services/research_agent.py`
**Changes**:
- Added `web_search_tool` parameter (placeholder for future integration)
- Added `plan_context` to `AgentState` for existing portfolio awareness
- Updated `analyze_scenarios_node()` to:
  - Accept and use `plan_context`
  - Pass `web_search_tool` to LLM when available
- Updated `get_initial_state()` to include `plan_context`

### 2. `/backend/app/services/portfolio_optimizer.py`
**Changes**:
- **`_generate_llm_scenarios()`**: New method using LLM for scenario generation
  - Replaces hardcoded scenarios with AI-generated ones
  - Takes portfolio context into account
  - Generates Base/Bull/Bear cases with specific adjustments

- **`_generate_trajectory()`**: Helper for scenario trajectory generation

- **`_generate_llm_report()`**: Enhanced to return both:
  - `report`: Main analysis report
  - `follow_up_suggestions`: 3-4 suggested follow-up research questions

- **`_generate_scenario_forecasts()`**: Updated to:
  - Try LLM-powered scenarios first
  - Fall back to hardcoded scenarios if LLM fails

- **Optimization flow**: Updated to extract follow-up suggestions and store in metrics

### 3. `/backend/app/core/dependencies.py`
**Changes**:
- Added `get_plan_service()` dependency
- Added `get_research_agent()` dependency

### 4. `/backend/app/main.py`
**Changes**:
- Registered `plans_router` with prefix `/api`

---

## Key Features Implemented

### 1. Plan Management
- ✅ Create, read, update, delete investment plans
- ✅ Plans linked to user_id (prepared for multi-user future)
- ✅ Store optimization results with plans
- ✅ Store research history with plans
- ✅ Tax account configuration (NISA, iDeCo support)
- ✅ Recurring investment configuration
- ✅ Risk preference configuration

### 2. Research Agent Enhancements
- ✅ Web search tool placeholder (ready for future integration)
- ✅ Plan context awareness
- ✅ Can analyze existing portfolios
- ✅ Follow-up suggestions generation
- ✅ Research history preservation

### 3. Code Quality Improvements
- ✅ Reduced scenario generation duplication
- ✅ Portfolio optimizer now uses LLM for scenarios
- ✅ Shared utilities for trajectory generation
- ✅ Proper separation of concerns

### 4. API Infrastructure
- ✅ RESTful API for plan management
- ✅ Research endpoint with plan context
- ✅ Follow-up suggestions exposed via API

---

## Integration Points

### For Portfolio Optimizer
When optimization completes, it now:
1. Generates LLM-powered scenarios (not hardcoded)
2. Creates an LLM report with follow-up suggestions
3. Can be saved as a plan via `plan_service.attach_optimization_result()`

### For Research Agent
When triggered from a plan:
1. Receives portfolio context (existing allocation, risk preference)
2. Can access web search (when tool is available)
3. Generates scenarios with plan-aware context
4. Saves results to plan's research history

### For UI/Frontend (Future Implementation)
The frontend should:
1. Show plan selection screen on load
2. Display plan detail view with optimization results
3. Show follow-up suggestions after optimization
4. Provide deep-dive buttons on metrics
5. Allow running research on plan context
6. Support plan creation/editing

---

## Configuration Examples

### Creating a Plan with NISA Configuration
```python
await plan_service.create_plan(
    user_id="default",
    name="Retirement Portfolio",
    description="Long-term growth with NISA tax benefits",
    risk_preference=RiskProfile.MODERATE,
    initial_amount=1000000,
    currency="JPY"
)

# Later attach tax accounts
plan.tax_accounts = [
    TaxAccount(
        account_type=TaxAccountType.NISA_GENERAL,
        name="NISA General Account",
        annual_limit=1200000,  # 1.2M JPY
        dividend_tax_rate=0.0,
        capital_gains_tax_rate=0.0
    ),
    TaxAccount(
        account_type=TaxAccountType.IDECO,
        name="iDeCo",
        annual_limit=144000,  # Monthly limit varies by age
        dividend_tax_rate=0.0,
        capital_gains_tax_rate=0.0,
        contribution_deductible=True
    )
]
```

### Setting Up Recurring Investment
```python
plan.recurring_investment = RecurringInvestment(
    enabled=True,
    frequency=InvestmentFrequency.MONTHLY,
    amount=50000,
    currency="JPY",
    dividend_reinvestment=True
)
```

---

## Next Steps (Recommended Priority)

### Phase 1: UI Integration
1. Create plan selection screen
2. Create plan detail view
3. Display follow-up suggestions
4. Add deep-dive buttons on metrics
5. Implement research agent trigger

### Phase 2: Portfolio Optimizer Integration
1. Modify optimizer to create/save plans automatically
2. Update optimization endpoint to return plan_id
3. Link optimization jobs to plans

### Phase 3: Enhanced Features
1. Implement web search tool integration
2. Add tax-aware optimization (account allocation)
3. Add DCA optimization (timing and amount)
4. Implement recurring investment tracking

### Phase 4: Additional Agents
1. Stress Testing Agent (highest priority)
2. Rebalancing Assistant
3. Tax Optimization Agent

---

## Backward Compatibility

- ✅ All existing API endpoints unchanged
- ✅ Research agent still works without plan context
- ✅ Portfolio optimizer falls back to hardcoded scenarios if LLM fails
- ✅ Default user_id="default" for single-user mode

---

## Testing Checklist

- [ ] Create plan via API
- [ ] List plans via API
- [ ] Update plan metadata
- [ ] Attach optimization result to plan
- [ ] Run research agent on plan
- [ ] Verify follow-up suggestions generation
- [ ] Test with existing portfolio context
- [ ] Test tax account configuration
- [ ] Test recurring investment configuration

---

## Notes

- User authentication not yet implemented (uses "default" user)
- Web search tool is a placeholder awaiting Tavily/Google API integration
- Tax optimization logic not yet implemented (only configuration structure)
- DCA automation not yet implemented (only configuration structure)
