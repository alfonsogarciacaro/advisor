# User Stories for ETF Portfolio Advisor

## Overview

This document outlines user stories organized by feature area. Each story follows the format:
- **Title**: Clear description
- **As a**: User role
- **I want**: Goal
- **So that**: Benefit
- **Acceptance Criteria**: Testable conditions
- **Playwright Test**: Reference to test spec

These stories can be transformed into Playwright integration tests in `/frontend/tests/`.

---

## 1. Plan Management

### US-PM-01: Create First Investment Plan
**As a** new user
**I want to** create my first investment plan
**So that** I can start organizing my investment strategy

**Acceptance Criteria:**
- User sees empty state when no plans exist
- "Create Your First Plan" button is visible
- Modal opens with name, description, risk preference fields
- Plan is created and appears in the list
- User is redirected to plan detail view

**Playwright Test**: `plans/create-first-plan.spec.ts`

---

### US-PM-02: Create Multiple Plans for Different Goals
**As a** investor
**I want to** create separate plans for different goals
**So that** I can track retirement vs education savings separately

**Acceptance Criteria:**
- Can create plan named "Retirement Portfolio"
- Can create plan named "Education Fund"
- Both plans appear in the list
- Each plan maintains separate optimization results

**Playwright Test**: `plans/multiple-plans.spec.ts`

---

### US-PM-03: Delete Plan with Confirmation
**As a** user
**I want to** delete a plan I no longer need
**So that** my plan list stays organized

**Acceptance Criteria:**
- Delete button appears on plan card
- Confirmation dialog shows plan name
- Cancel button aborts deletion
- Confirm button deletes plan
- Plan disappears from list
- Success message or redirect to plan list

**Playwright Test**: `plans/delete-plan.spec.ts`

---

### US-PM-04: Switch Between Plans
**As a** user with multiple plans
**I want to** switch between plans
**So that** I can review different investment strategies

**Acceptance Criteria:**
- Clicking a plan card opens detail view
- Back button returns to plan list
- Last viewed plan is remembered (optional)
- Each plan shows correct data

**Playwright Test**: `plans/switch-plans.spec.ts`

---

## 2. Portfolio Optimization

### US-PO-01: Run Basic Optimization
**As a** user
**I want to** optimize my portfolio allocation
**So that** I get mathematically optimal returns for my risk level

**Acceptance Criteria:**
- Input fields for amount and currency
- "Optimize Portfolio" button starts optimization
- Status badge shows progress stages
- Final results show optimal allocation
- Metrics: expected return, volatility, Sharpe ratio

**Playwright Test**: `optimization/basic-optimization.spec.ts`

---

### US-PO-02: View Efficient Frontier Chart
**As a** user
**I want to** see the efficient frontier visualization
**So that** I understand the risk-return tradeoff

**Acceptance Criteria:**
- Chart displays after optimization completes
- X-axis: Volatility, Y-axis: Return
- Efficient frontier line is visible
- Current optimal portfolio is marked
- Tooltip shows values on hover

**Playwright Test**: `optimization/efficient-frontier.spec.ts`

---

### US-PO-03: View Scenario Forecasts
**As a** user
**I want to** see bull/bear/base case scenarios
**So that** I understand potential outcomes

**Acceptance Criteria:**
- Three scenarios display: Base, Bull, Bear
- Each shows probability, description, expected value
- Line chart shows trajectory over time
- Color coding: Green (Bull), Blue (Base), Red (Bear)

**Playwright Test**: `optimization/scenario-forecasts.spec.ts`

---

### US-PO-04: Optimize with Different Amounts
**As a** user
**I want to** try different investment amounts
**So that** I can plan for different budget levels

**Acceptance Criteria:**
- Can change amount input
- Can change currency dropdown
- Optimization runs with new values
- Results scale appropriately

**Playwright Test**: `optimization/vary-amounts.spec.ts`

---

## 3. Account Management

### US-AM-01: Add NISA Account
**As a** Japanese investor
**I want to** add a NISA Growth account
**So that** I can track my tax-advantaged investments

**Acceptance Criteria:**
- "Add Account" button opens modal
- Account type dropdown includes "NISA Growth"
- Annual limit pre-fills (¥1.8M)
- Account appears in list with correct badge
- Progress bar shows available space

**Playwright Test**: `accounts/add-nisa-account.spec.ts`

---

### US-AM-02: Configure Multiple Account Types
**As a** tax-conscious investor
**I want to** set up NISA + Taxable accounts
**So that** I can optimize tax placement

**Acceptance Criteria:**
- Can add NISA Growth (¥1.8M limit)
- Can add NISA General (¥1.2M limit)
- Can add Taxable (unlimited)
- Summary shows total: ¥3M/year capacity
- Each account shows tax rate (0% vs 20.315%)

**Playwright Test**: `accounts/multi-account-setup.spec.ts`

---

### US-AM-03: Edit Account Limits
**As a** user
**I want to** update my account balance and available space
**So that** the system tracks my actual capacity

**Acceptance Criteria:**
- Edit button on account card
- Can update current balance
- Can update available space
- Progress bar reflects changes
- Summary totals update

**Playwright Test**: `accounts/edit-account.spec.ts`

---

### US-AM-04: Delete Unused Account
**As a** user
**I want to** remove an account I don't use
**So that** my accounts list is accurate

**Acceptance Criteria:**
- Delete button on account card
- Confirmation dialog shows account name
- Account is removed from list
- Summary totals update

**Playwright Test**: `accounts/delete-account.spec.ts`

---

## 4. Research Agent Integration

### US-RA-01: View Follow-up Suggestions
**As a** user
**I want to** see suggested research questions
**So that** I can explore my portfolio further

**Acceptance Criteria:**
- After optimization, 3-4 suggestions appear
- Each suggestion is clickable
- Clicking runs research agent
- Results display below

**Playwright Test**: `research/follow-up-suggestions.spec.ts`

---

### US-RA-02: Ask Custom Research Question
**As a** user
**I want to** ask a specific question about my portfolio
**So that** I get personalized insights

**Acceptance Criteria:**
- Text input for custom question
- Submit button or Enter key to send
- Loading state during research
- Results display when complete
- New follow-up suggestions generated

**Playwright Test**: `research/custom-question.spec.ts`

---

### US-RA-03: Chain Research Conversations
**As a** user
**I want to** ask follow-up questions
**So that** I can dive deeper into topics

**Acceptance Criteria:**
- Research results include new suggestions
- Clicking suggestion pre-fills input
- Previous research context is maintained
- Can ask multiple questions in sequence

**Playwright Test**: `research/research-conversation.spec.ts`

---

### US-RA-04: Deep Dive into Metrics
**As a** user
**I want to** understand specific metrics in detail
**So that** I can make informed decisions

**Acceptance Criteria:**
- Deep-dive buttons next to key metrics
- "Analyze" on Expected Return
- "Deep Dive" on Volatility
- "Explain" on Sharpe Ratio
- Clicking pre-fills research query

**Playwright Test**: `research/deep-dive-metrics.spec.ts`

---

## 5. Settings & Preferences

### US-SP-01: Update Plan Risk Preference
**As a** user
**I want to** change my risk tolerance
**So that** the optimization matches my comfort level

**Acceptance Criteria:**
- Settings tab shows risk dropdown
- All 5 levels available
- Can save changes
- Badge updates to show new risk level

**Playwright Test**: `settings/update-risk.spec.ts`

---

### US-SP-02: Edit Plan Name and Description
**As a** user
**I want to** update my plan details
**So that** my plans are clearly labeled

**Acceptance Criteria:**
- Can edit plan name
- Can edit description
- Changes save immediately or on button click
- Updates reflect in plan list

**Playwright Test**: `settings/edit-plan-details.spec.ts`

---

### US-SP-03: Add Plan Notes
**As a** user
**I want to** add notes to my plan
**So that** I remember my investment rationale

**Acceptance Criteria:**
- Notes textarea in Settings tab
- Can save multi-line notes
- Notes persist across sessions

**Playwright Test**: `settings/plan-notes.spec.ts`

---

## 6. AI Report & Analysis

### US-AI-01: View AI-Generated Report
**As a** user
**I want to** read an AI analysis of my portfolio
**So that** I understand the recommendations

**Acceptance Criteria:**
- Report displays after optimization
- Markdown formatting renders correctly
- Sections: Overview, Risk, Returns, Recommendations
- Loading state shows during generation

**Playwright Test**: `ai-report/view-report.spec.ts`

---

### US-AI-02: Apply LLM-Suggested Constraints
**As a** user
**I want to** apply AI-suggested portfolio constraints
**So that** I can improve flawed allocations

**Acceptance Criteria:**
- LLM identifies concentration issues
- Suggests specific constraints (e.g., "Max Gold 10%")
- "Apply" button adds constraint
- "Re-optimize" button runs new optimization

**Playwright Test**: `ai-report/apply-constraints.spec.ts`

---

## 7. News & Market Data

### US-NW-01: View Financial News
**As a** user
**I want to** see latest financial news
**So that** I stay informed about market conditions

**Acceptance Criteria:**
- News displays on homepage
- Shows "Updated every 12h" badge
- At least 3 news items visible
- Each has title, summary, link

**Playwright Test**: `news/view-news.spec.ts` (Already exists)

---

### US-NW-02: Refresh News Feed
**As a** user
**I want to** refresh news manually
**So that** I get latest updates

**Acceptance Criteria:**
- Refresh button visible
- Clicking reloads news
- Loading state during refresh
- New items appear if available

**Playwright Test**: `news/refresh-news.spec.ts`

---

## 8. Error Handling

### US-EH-01: Handle Optimization Failure
**As a** user
**I want to** see clear error messages
**So that** I understand what went wrong

**Acceptance Criteria:**
- Error alert displays on failure
- Error message is descriptive
- Can retry optimization
- Error state clears on retry

**Playwright Test**: `errors/optimization-failure.spec.ts`

---

### US-EH-02: Handle Network Errors
**As a** user
**I want to** see feedback on network issues
**So that** I know the app is having trouble

**Acceptance Criteria:**
- Network errors show user-friendly message
- Retry option available
- App doesn't crash on network error

**Playwright Test**: `errors/network-error.spec.ts`

---

## 9. Responsive Design

### US-RD-01: View Plans on Mobile
**As a** mobile user
**I want to** manage plans on my phone
**So that** I can invest anywhere

**Acceptance Criteria:**
- Plan list is readable on mobile
- Cards stack vertically
- Touch targets are large enough
- Modals fit on small screens

**Playwright Test**: `responsive/mobile-plans.spec.ts`

---

### US-RD-02: View Optimization on Tablet
**As a** tablet user
**I want to** see charts and tables clearly
**So that** I can analyze results comfortably

**Acceptance Criteria:**
- Charts are responsive
- Tables are scrollable horizontally
- Navigation works with touch

**Playwright Test**: `responsive/tablet-optimization.spec.ts`

---

## 10. Performance

### US-PF-01: Fast Plan Loading
**As a** user
**I want** plans to load quickly
**So that** I don't wait unnecessarily

**Acceptance Criteria:**
- Plan list loads in <2 seconds
- Plan detail loads in <1 second
- Loading skeletons show during fetch

**Playwright Test**: `performance/plan-loading.spec.ts`

---

### US-PF-02: Optimistic UI Updates
**As a** user
**I want** immediate feedback on my actions
**So that** the app feels responsive

**Acceptance Criteria:**
- Button clicks show immediate feedback
- Form updates reflect instantly
- Optimistic updates roll back on error

**Playwright Test**: `performance/optimistic-updates.spec.ts`

---

## Test Implementation Priority

### High Priority (Core Flows)
1. US-PM-01: Create First Plan
2. US-PO-01: Run Basic Optimization
3. US-RA-01: View Follow-up Suggestions
4. US-AM-01: Add NISA Account

### Medium Priority (Important Features)
5. US-PO-02: Efficient Frontier Chart
6. US-PO-03: Scenario Forecasts
7. US-RA-02: Custom Research Question
8. US-AI-01: View AI Report

### Low Priority (Nice to Have)
9. US-SP-03: Plan Notes
10. US-NW-02: Refresh News
11. US-RD-01/02: Responsive Design
12. US-PF-01/02: Performance Tests

---

## Converting to Playwright Tests

Each user story maps to a Playwright test file:

```
frontend/tests/
├── plans/
│   ├── create-first-plan.spec.ts
│   ├── multiple-plans.spec.ts
│   ├── delete-plan.spec.ts
│   └── switch-plans.spec.ts
├── optimization/
│   ├── basic-optimization.spec.ts
│   ├── efficient-frontier.spec.ts
│   ├── scenario-forecasts.spec.ts
│   └── vary-amounts.spec.ts
├── accounts/
│   ├── add-nisa-account.spec.ts
│   ├── multi-account-setup.spec.ts
│   ├── edit-account.spec.ts
│   └── delete-account.spec.ts
├── research/
│   ├── follow-up-suggestions.spec.ts
│   ├── custom-question.spec.ts
│   ├── research-conversation.spec.ts
│   └── deep-dive-metrics.spec.ts
├── settings/
│   ├── update-risk.spec.ts
│   ├── edit-plan-details.spec.ts
│   └── plan-notes.spec.ts
├── ai-report/
│   ├── view-report.spec.ts
│   └── apply-constraints.spec.ts
├── news/
│   ├── view-news.spec.ts
│   └── refresh-news.spec.ts
├── errors/
│   ├── optimization-failure.spec.ts
│   └── network-error.spec.ts
├── responsive/
│   ├── mobile-plans.spec.ts
│   └── tablet-optimization.spec.ts
└── performance/
    ├── plan-loading.spec.ts
    └── optimistic-updates.spec.ts
```

---

## Example Test Implementation

### `plans/create-first-plan.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('Create First Investment Plan', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
    });

    test('should show empty state when no plans exist', async ({ page }) => {
        // Should see "No plans yet" message
        await expect(page.getByText('No plans yet')).toBeVisible();
        await expect(page.getByText('Create Your First Plan')).toBeVisible();
    });

    test('should open create plan modal', async ({ page }) => {
        // Click "Create Your First Plan" button
        await page.getByRole('button', { name: 'Create Your First Plan' }).click();

        // Modal should appear
        await expect(page.getByRole('dialog')).toBeVisible();
        await expect(page.getByRole('heading', { name: 'Create New Investment Plan' })).toBeVisible();

        // Form fields should be present
        await expect(page.getByLabel('Plan Name')).toBeVisible();
        await expect(page.getByLabel('Description (optional)')).toBeVisible();
        await expect(page.getByLabel('Risk Preference')).toBeVisible();
    });

    test('should create plan with valid data', async ({ page }) => {
        // Open modal
        await page.getByRole('button', { name: 'Create Your First Plan' }).click();

        // Fill form
        await page.getByLabel('Plan Name').fill('Retirement Portfolio');
        await page.getByLabel('Description (optional)').fill('Long-term retirement savings');
        await page.getByLabel('Risk Preference').selectOption('moderate');

        // Submit
        await page.getByRole('button', { name: 'Create Plan' }).click();

        // Modal should close
        await expect(page.getByRole('dialog')).not.toBeVisible();

        // Plan should appear in list
        await expect(page.getByText('Retirement Portfolio')).toBeVisible();

        // Risk badge should be visible
        await expect(page.getByText('Moderate')).toBeVisible();
    });

    test('should show validation error for empty name', async ({ page }) => {
        // Open modal
        await page.getByRole('button', { name: 'Create Your First Plan' }).click();

        // Try to submit without name
        await page.getByRole('button', { name: 'Create Plan' }).click();

        // Error should appear
        await expect(page.getByText('Please enter a plan name')).toBeVisible();
    });
});
```

---

## Test Data Strategy

### Mock Data for Tests

```typescript
// test/fixtures/plans.ts
export const mockPlans = {
    empty: [],
    single: [
        {
            plan_id: 'plan-1',
            name: 'Retirement Portfolio',
            risk_preference: 'moderate',
            optimization_result: null,
            research_history: [],
        }
    ],
    multiple: [
        {
            plan_id: 'plan-1',
            name: 'Retirement Portfolio',
            risk_preference: 'moderate',
        },
        {
            plan_id: 'plan-2',
            name: 'Education Fund',
            risk_preference: 'conservative',
        }
    ]
};

// test/fixtures/optimization.ts
export const mockOptimizationResult = {
    job_id: 'job-1',
    status: 'completed',
    optimal_portfolio: [
        { ticker: 'SPY', weight: 0.40, amount: 40000 },
        { ticker: 'VEA', weight: 0.30, amount: 30000 },
        { ticker: 'GLD', weight: 0.30, amount: 30000 }
    ],
    metrics: {
        expected_annual_return: 0.08,
        annual_volatility: 0.12,
        sharpe_ratio: 0.67
    },
    scenarios: [
        { name: 'Base Case', probability: 0.6, expected_return: 0.08 },
        { name: 'Bull Case', probability: 0.2, expected_return: 0.15 },
        { name: 'Bear Case', probability: 0.2, expected_return: -0.05 }
    ]
};
```

---

## Test Execution

```bash
# Run all tests
npx playwright test

# Run specific suite
npx playwright test plans/

# Run specific test
npx playwright test plans/create-first-plan.spec.ts

# Run with UI
npx playwright test --ui

# Run with debug
npx playwright test --debug

# Run headed (see browser)
npx playwright test --headed
```

---

## Coverage Goals

| Feature Area | Stories | Target Coverage |
|--------------|---------|-----------------|
| Plan Management | 4 | 100% |
| Optimization | 4 | 100% |
| Accounts | 4 | 100% |
| Research | 4 | 80% |
| Settings | 3 | 60% |
| AI Report | 2 | 50% |
| News | 2 | 50% |
| Errors | 2 | 100% |
| Responsive | 2 | 40% |
| Performance | 2 | 20% |

**Overall Target**: 70%+ coverage for critical paths
