import { test, expect } from '@playwright/test';
import { createPlan } from '../test-utils';

/**
 * US-MA-01: Register Existing Asset Holdings
 *
 * Acceptance Criteria:
 * - "Edit Portfolio" button is always visible on plan detail page
 * - Modal opens showing current holdings (if any) grouped by account type
 * - Can add asset by selecting: ETF ticker, account type, monetary value (¥)
 * - Validation prevents exceeding account limits (e.g., NISA Growth ¥1.8M/year)
 * - Holdings display grouped by account with totals
 * - Progress bar shows usage vs limit for each account
 * - "Register Existing Assets" prompt shown for new plans before first optimization
 *
 * SKIPPED: Tests require working PortfolioEditor with backend ETF data.
 * The "Add Asset" button doesn't create new rows in test environment.
 *
 * TODO: Fix by either:
 * - Mocking getAvailableEtfs API response
 * - Ensuring test backend has proper ETF configurations
 * - Fixing PortfolioEditor state management
 */
test.describe('Register Existing Asset Holdings', () => {
    test.beforeEach(async ({ page }) => {
        // Create a unique plan for each test
        const planName = `Portfolio Test ${Date.now()}`;
        await createPlan(page, planName);
    });

    test('should display "Edit Portfolio" button on plan detail page', async ({ page }) => {
        // Verify Edit Portfolio button is visible
        const editButton = page.getByRole('button', { name: /Edit Portfolio/i });
        await expect(editButton).toBeVisible();
    });

    test('should show "Register Existing Assets" prompt for new plan', async ({ page }) => {
        // New plans without optimization or holdings should show prompt
        await expect(page.getByText(/Do you have existing investments/i)).toBeVisible();
        await expect(page.getByRole('button', { name: /Register Existing Assets/i })).toBeVisible();
    });

    test('should open portfolio editor modal when clicking Edit Portfolio', async ({ page }) => {
        await page.getByRole('button', { name: /Edit Portfolio/i }).click();

        // Modal should appear
        await expect(page.getByRole('heading', { name: /Edit Portfolio Holdings/i })).toBeVisible();

        // Should have the add asset button
        await expect(page.getByRole('button', { name: /Add Asset/i })).toBeVisible();
    });

    test('should add a new asset holding', async ({ page }) => {
        await page.getByRole('button', { name: /Edit Portfolio/i }).click();

        // Add a new holding
        await page.getByRole('button', { name: /Add Asset/i }).click();

        // Should see a new holding row - use label text to find selects/inputs
        const etfSelect = page.getByLabel(/^ETF$/i).first();
        await expect(etfSelect).toBeVisible();

        // Select an ETF (assumes there are available ETFs)
        await etfSelect.selectOption({ index: 1 }); // Select first non-empty option

        // Select account type
        await page.getByLabel(/^Account$/i).first().selectOption('nisa_growth');

        // Enter monetary value
        await page.getByLabel(/Value \(JPY\)/i).first().fill('500000');

        // Save
        await page.getByRole('button', { name: /Save Portfolio/i }).click();

        // Modal should close
        await expect(page.getByRole('heading', { name: /Edit Portfolio Holdings/i })).not.toBeVisible();

        // Verify holdings are displayed
        await expect(page.getByText(/Current Holdings/i)).toBeVisible();
    });

    test('should display holdings grouped by account type', async ({ page }) => {
        // Add a holding first
        await page.getByRole('button', { name: /Edit Portfolio/i }).click();
        await page.getByRole('button', { name: /Add Asset/i }).click();

        // Add to NISA Growth
        await page.getByLabel(/^ETF$/i).first().selectOption({ index: 1 });
        await page.getByLabel(/^Account$/i).first().selectOption('nisa_growth');
        await page.getByLabel(/Value \(JPY\)/i).first().fill('500000');

        // Add another asset to a different account
        await page.getByRole('button', { name: /Add Asset/i }).click();
        await page.getByLabel(/^ETF$/i).last().selectOption({ index: 2 });
        await page.getByLabel(/^Account$/i).last().selectOption('taxable');
        await page.getByLabel(/Value \(JPY\)/i).last().fill('300000');

        await page.getByRole('button', { name: /Save Portfolio/i }).click();

        // Should see grouped holdings - use first() to avoid matching dropdown options
        await expect(page.getByText(/NISA Growth/i).first()).toBeVisible();
        await expect(page.getByText(/Taxable/i).first()).toBeVisible();

        // Should see total portfolio value
        await expect(page.getByText(/Total Portfolio Value/i)).toBeVisible();
    });

    test('should show progress bar for account with limits', async ({ page }) => {
        await page.getByRole('button', { name: /Edit Portfolio/i }).click();
        await page.getByRole('button', { name: /Add Asset/i }).click();

        // Add to NISA Growth (has annual limit)
        await page.getByLabel(/^ETF$/i).first().selectOption({ index: 1 });
        await page.getByLabel(/^Account$/i).first().selectOption('nisa_growth');
        await page.getByLabel(/Value \(JPY\)/i).first().fill('900000');

        // Should see account usage indicator while editing
        await expect(page.locator('progress').first()).toBeVisible();

        await page.getByRole('button', { name: /Save Portfolio/i }).click();

        // After save, should see progress bar in holdings display
        await expect(page.locator('progress').first()).toBeVisible();
    });

    test('should validate against account limits', async ({ page }) => {
        await page.getByRole('button', { name: /Edit Portfolio/i }).click();
        await page.getByRole('button', { name: /Add Asset/i }).click();

        // Try to add more than NISA Growth limit (¥1,800,000)
        await page.getByLabel(/^ETF$/i).first().selectOption({ index: 1 });
        await page.getByLabel(/^Account$/i).first().selectOption('nisa_growth');
        await page.getByLabel(/Value \(JPY\)/i).first().fill('2000000');

        // Should see warning about over limit
        await expect(page.getByText(/Over limit/i)).toBeVisible();

        // Save button might be disabled or show error on click
        const saveButton = page.getByRole('button', { name: /Save Portfolio/i });
        await saveButton.click();

        // Should see validation error
        await expect(page.getByText(/Validation Error/i).or(page.getByText(/exceeds/i))).toBeVisible();
    });

    test('should allow editing existing holdings', async ({ page }) => {
        // Add a holding first
        await page.getByRole('button', { name: /Edit Portfolio/i }).click();
        await page.getByRole('button', { name: /Add Asset/i }).click();

        await page.getByLabel(/^ETF$/i).first().selectOption({ index: 1 });
        await page.getByLabel(/^Account$/i).first().selectOption('nisa_growth');
        await page.getByLabel(/Value \(JPY\)/i).first().fill('500000');
        await page.getByRole('button', { name: /Save Portfolio/i }).click();

        // Re-open editor
        await page.getByRole('button', { name: /Edit Portfolio/i }).click();

        // Should see existing holding
        const valueInput = page.getByLabel(/Value \(JPY\)/i).first();
        await expect(valueInput).toHaveValue('500000');

        // Edit the value
        await valueInput.fill('750000');
        await page.getByRole('button', { name: /Save Portfolio/i }).click();

        // Verify update - reopen to check
        await page.getByRole('button', { name: /Edit Portfolio/i }).click();
        await expect(page.getByLabel(/Value \(JPY\)/i).first()).toHaveValue('750000');
    });

    test('should allow removing holdings', async ({ page }) => {
        // Add a holding first
        await page.getByRole('button', { name: /Edit Portfolio/i }).click();
        await page.getByRole('button', { name: /Add Asset/i }).click();

        await page.getByLabel(/^ETF$/i).first().selectOption({ index: 1 });
        await page.getByLabel(/^Account$/i).first().selectOption('nisa_growth');
        await page.getByLabel(/Value \(JPY\)/i).first().fill('500000');
        await page.getByRole('button', { name: /Save Portfolio/i }).click();

        // Re-open editor
        await page.getByRole('button', { name: /Edit Portfolio/i }).click();

        // Click remove button
        await page.getByRole('button', { name: /Remove/i }).first().click();

        // Should only see Add Asset button (no holdings)
        await expect(page.getByLabel(/^ETF$/i)).not.toBeVisible();

        // Cancel instead of save (empty portfolio cannot be saved)
        await page.getByRole('button', { name: /Cancel/i }).click();

        // After removing all assets, Current Holdings might not be visible
        // Check the plan page reflects the state
    });

    test('should cancel without saving changes', async ({ page }) => {
        // Add a holding first
        await page.getByRole('button', { name: /Edit Portfolio/i }).click();
        await page.getByRole('button', { name: /Add Asset/i }).click();

        await page.getByLabel(/^ETF$/i).first().selectOption({ index: 1 });
        await page.getByLabel(/^Account$/i).first().selectOption('nisa_growth');
        await page.getByLabel(/Value \(JPY\)/i).first().fill('500000');

        // Cancel instead of save
        await page.getByRole('button', { name: /Cancel/i }).click();

        // Modal should close
        await expect(page.getByRole('heading', { name: /Edit Portfolio Holdings/i })).not.toBeVisible();

        // Should not see holdings
        await expect(page.getByText(/Current Holdings/i)).not.toBeVisible();
    });

    test('should show total value across all accounts', async ({ page }) => {
        await page.getByRole('button', { name: /Edit Portfolio/i }).click();

        // Add multiple holdings
        await page.getByRole('button', { name: /Add Asset/i }).click();
        await page.getByLabel(/^ETF$/i).first().selectOption({ index: 1 });
        await page.getByLabel(/^Account$/i).first().selectOption('nisa_growth');
        await page.getByLabel(/Value \(JPY\)/i).first().fill('500000');

        await page.getByRole('button', { name: /Add Asset/i }).click();
        await page.getByLabel(/^ETF$/i).last().selectOption({ index: 2 });
        await page.getByLabel(/^Account$/i).last().selectOption('taxable');
        await page.getByLabel(/Value \(JPY\)/i).last().fill('300000');

        // Should see total in modal
        await expect(page.getByText(/Total:/i)).toBeVisible();
        await expect(page.getByText(/800,000/i).or(page.getByText(/¥800,000/i))).toBeVisible();

        await page.getByRole('button', { name: /Save Portfolio/i }).click();

        // After save, should see total portfolio value
        await expect(page.getByText(/Total Portfolio Value/i)).toBeVisible();
    });
});
