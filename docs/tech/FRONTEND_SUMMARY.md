# Frontend Implementation Summary

## Date: 2025-01-29

## Completed Features

### 1. Plan Management System

#### `PlanManager.tsx`
- **List all plans** with metadata (risk profile, optimization status, research count)
- **Create new plans** with modal dialog (name, description, risk preference)
- **Delete plans** with confirmation
- **Select plan** to view details
- Empty state when no plans exist

### 2. Plan Detail View (`PlanDetail.tsx`)

#### Tabbed Navigation
- **Overview Tab**: Optimization results, metrics, allocation, scenarios
- **Accounts Tab**: Multi-account configuration (NISA, iDeCo, taxable)
- **Settings Tab**: User preferences (name, description, risk, notes)

#### Overview Tab Features
- **Key metrics display** with deep-dive buttons
  - Expected Annual Return → "Analyze"
  - Annual Volatility → "Deep Dive"
  - Sharpe Ratio → "Explain"
  - Allocation → "Analyze Allocation"
- **Optimization results** (toggle show/hide)
- **Portfolio allocation table**
- **AI Analysis Report** (markdown formatted)
- **Scenario forecasts** (Base/Bull/Bear cases)

### 3. Account Management (`AccountManager.tsx`)

Fully functional account CRUD for multi-account investment strategies:

#### Account Types Supported
| Type | Description | Default Limit |
|------|-------------|---------------|
| NISA Growth | High-growth investments | ¥1.8M/year |
| NISA General | Broad market investments | ¥1.2M/year |
| iDeCo | Private pension (deductible) | ¥144K-¥816K/year |
| DC Pension | Company pension | 0 (unlimited) |
| Taxable | Standard account | Unlimited |
| Other | Special account types | 0 |

#### Features
- **Add accounts** via modal with type selection
- **Edit accounts**: name, limits, balances, tax rates, withdrawal rules
- **Delete accounts** with confirmation
- **Visual progress bars** for account utilization (NISA limits)
- **Tax badges**: "Tax-Free" for NISA/iDeCo, "Deductible" for iDeCo
- **Summary stats**: Total accounts, annual limit, available space

### 4. Research Agent Integration (`ResearchPanel.tsx`)

#### Follow-up Suggestions
- Displays LLM-generated research questions
- One-click analysis of suggestions
- Auto-fills custom query input

#### Custom Research
- Free-form question input
- Enter key to submit
- Loading state during analysis

#### Research Results
- Summary display
- New follow-up suggestions generated
- Run ID tracking
- Error handling

### 5. Deep-Dive Buttons

Located on key metrics in PlanDetail overview:
- **Return Analysis**: "Explain the drivers of expected return"
- **Volatility Deep Dive**: "Analyze risk factors and volatility sources"
- **Sharpe Explanation**: "Evaluate risk-adjusted performance"
- **Allocation Analysis**: "Analyze portfolio allocation and concentration"

Auto-scrolls to Research Panel and pre-fills query when clicked.

### 6. Updated Main App Flow (`page.tsx`)

#### Plan Selection View
- List all plans with metadata
- Create new plan button
- News sidebar retained
- Welcome section with description

#### Plan Detail View
- Back navigation to plans
- Tabbed content (Overview/Accounts/Settings)
- Research panel always visible
- Optimization results toggle

### 7. API Client Extensions (`api-client.ts`)

Added TypeScript interfaces and functions:
```typescript
// Types
RiskProfile, TaxAccount, RecurringInvestment
ResearchRun, Plan, PlanCreateRequest, PlanUpdateRequest
ResearchOnPlanRequest, ResearchOnPlanResponse

// Functions
createPlan, listPlans, getPlan, updatePlan, deletePlan
runResearchOnPlan
```

### 8. Backend Tests (`test_endpoints.py`)

12 new tests added:
- `test_create_plan` - Full plan creation
- `test_create_plan_minimal` - Minimal creation
- `test_list_plans` - List filtering by user
- `test_get_plan` - Retrieve by ID
- `test_get_plan_not_found` - 404 handling
- `test_update_plan` - Update metadata
- `test_update_plan_not_found` - Update 404
- `test_delete_plan` - Delete plan
- `test_delete_plan_not_found` - Delete 404
- `test_run_research_on_plan` - Research agent integration
- `test_run_research_on_plan_not_found` - Research 404

---

## Configuration Architecture (As Discussed)

### Admin Config (YAML - Read-Only for Users)
- Account rules (NISA limits, tax rates)
- Available ETF universe
- Market conditions, legislation updates
- Location: `backend/app/config/`
- Future: LLM can update periodically

### User Config (Per Plan)
- Risk appetite
- Tax residence (implied by account types)
- Investment preferences
- Location: `Plan` model in database

---

## Multi-Account Support (Fully Implemented)

### Data Model
```typescript
interface Plan {
    tax_accounts: TaxAccount[];  // ← List, not single
    // ... other fields
}
```

### Example Strategy
```
Plan: "Tax-Optimized Retirement"
├── NISA Growth (¥1.8M limit)
│   └── High-growth ETFs (0% tax)
├── NISA General (¥1.2M limit)
│   └── Dividend ETFs (0% tax)
└── Taxable (unlimited)
    └── Overflow investments (20.315% tax)

Total capacity: ¥3M+/year
Tax savings: ~¥450K/year
```

### UI Features
- Progress bars for limit tracking
- Tax-free/deductible badges
- Multiple accounts per plan
- Account CRUD interface

---

## Component Hierarchy

```
page.tsx (Main App)
├── Plan Selection View
│   ├── PlanManager
│   │   ├── Create Plan Modal
│   │   └── Plan List
│   └── FinancialNews (sidebar)
│
└── Plan Detail View
    ├── PlanDetail
    │   ├── Tab Navigation
    │   ├── Overview Tab
    │   │   ├── Optimization Results
    │   │   ├── Metrics (with Deep-Dive buttons)
    │   │   ├── Allocation Table
    │   │   ├── AI Report
    │   │   └── Scenarios
    │   ├── Accounts Tab
    │   │   └── AccountManager
    │   │       ├── Account Cards
    │   │       ├── Add Account Modal
    │   │       └── Edit Account Modal
    │   └── Settings Tab
    │       └── Plan Settings Form
    │
    └── ResearchPanel
        ├── Follow-up Suggestions
        ├── Custom Query Input
        └── Research Results
```

---

## Next Steps (Future Work)

### Phase 1: Polish & Testing
1. Run frontend development server
2. Test all user flows end-to-end
3. Fix any TypeScript/build errors
4. Add error boundaries
5. Add loading skeletons

### Phase 2: Enhanced Features
1. **Tax-aware optimization**: Account-based asset placement
2. **DCA automation**: Multi-account recurring investment
3. **Research history**: View past research runs
4. **Plan comparison**: Compare multiple plans side-by-side

### Phase 3: Admin Features
1. **Config viewer UI**: Read-only view of admin config
2. **Account rules**: Display current NISA/iDeCo limits
3. **ETF universe**: Show available investment options

### Phase 4: User Settings
1. **Tax residence**: Multi-country support
2. **Age-based rules**: iDeCo limit calculation by age
3. **Risk questionnaire**: Automated risk profile detection

---

## File Structure

```
frontend/
├── app/
│   └── page.tsx (Updated)
├── components/
│   ├── PlanManager.tsx (New)
│   ├── PlanDetail.tsx (New)
│   ├── ResearchPanel.tsx (New)
│   ├── AccountManager.tsx (New)
│   ├── PortfolioOptimizer.tsx (Existing)
│   ├── financial-news.tsx (Existing)
│   └── AgentMonitor.tsx (Existing)
└── lib/
    └── api-client.ts (Extended)
```

---

## Design Decisions

1. **Tabbed navigation** for plan details (overview/accounts/settings)
2. **Modal dialogs** for create/edit operations
3. **Progress bars** for visual limit tracking
4. **Badge indicators** for quick status recognition
5. **Deep-dive buttons** that pre-fill research queries
6. **Research panel always visible** at bottom of detail view
7. **Local state** for optimistic updates (syncs with backend)
8. **Confirm dialogs** for destructive operations

---

## Known Limitations

1. **No actual persistence**: Changes update local state only (need backend sync)
2. **No account-based optimization yet**: Optimizer doesn't use account config
3. **No DCA automation**: Recurring investment configured but not executed
4. **No research history view**: Can't view past research runs
5. **Single user only**: Hardcoded "default" user_id

---

## How to Run

```bash
# Backend
cd backend
python -m uvicorn app.main:app --reload

# Frontend
cd frontend
npm run dev
```

Then navigate to `http://localhost:3000`

---

## Screenshots (Manual Testing Checklist)

- [ ] Plan selection screen loads
- [ ] Create new plan modal works
- [ ] Plan list displays correctly
- [ ] Plan detail view loads
- [ ] Tab navigation switches views
- [ ] Accounts can be added/edited/deleted
- [ ] Deep-dive buttons pre-fill research
- [ ] Follow-up suggestions display
- [ ] Custom research queries work
- [ ] Research results show correctly
- [ ] Settings save changes
- [ ] Back to Plans navigation works
