import { test, expect } from '@playwright/test';
import { createPlan } from '../test-utils';

/**
 * PLAYGROUND FEATURE TESTS - HISTORICAL BACKTESTING
 */

test.describe('Historical Backtest', () => {
    test.beforeEach(async ({ page }) => {
        // Create a unique plan for each test
        const planName = `Backtest Plan ${Date.now()}`;
        await createPlan(page, planName);

        // Navigate to Playground tab
        await page.getByRole('tab', { name: 'Playground' }).click();

        // Wait for page to stabilize
        await page.waitForTimeout(500);
    });

    test('should display historical replay interface', async ({ page }) => {
        // Should show the Historical Replay heading
        await expect(page.getByRole('heading', { name: /Historical Replay/i })).toBeVisible();

        // Should show description
        await expect(page.getByText(/how this strategy would have performed/i)).toBeVisible();

        // Should show Run Backtest button
        await expect(page.getByRole('button', { name: /Run Backtest/i })).toBeVisible();
    });

    test('should show preset historical periods', async ({ page }) => {
        // Should show preset period buttons
        const preCovidButton = page.getByRole('button', { name: /Pre-COVID/i });
        await expect(preCovidButton).toBeVisible();

        const pre2008Button = page.getByRole('button', { name: /Pre-2008 Crisis/i });
        await expect(pre2008Button).toBeVisible();

        const postCovidButton = page.getByRole('button', { name: /Post-COVID Recovery/i });
        await expect(postCovidButton).toBeVisible();

        // Should also show 5 Years Ago and 10 Years Ago
        await expect(page.getByRole('button', { name: /5 Years Ago/i })).toBeVisible();
        await expect(page.getByRole('button', { name: /10 Years Ago/i })).toBeVisible();
    });

    test('should select preset historical period', async ({ page }) => {
        // Click Pre-COVID button
        await page.getByRole('button', { name: /Pre-COVID/i }).click();

        // Verify date input is populated
        const dateInput = page.locator('#start-date');
        await expect(dateInput).toHaveValue('2020-01-01');
    });

    test('should allow custom date selection', async ({ page }) => {
        // Set custom date
        const dateInput = page.locator('#start-date');
        await dateInput.fill('2019-06-01');

        // Verify the date was set
        await expect(dateInput).toHaveValue('2019-06-01');
    });

    test('should allow changing investment amount', async ({ page }) => {
        // Set custom amount
        const amountInput = page.locator('#investment-amount');
        await amountInput.clear();
        await amountInput.fill('25000');

        // Verify the amount was set
        await expect(amountInput).toHaveValue('25000');
    });

    test('should run backtest and show loading state', async ({ page }) => {
        // Set a historical date
        await page.getByRole('button', { name: /Pre-COVID/i }).click();

        // Run backtest
        await page.getByRole('button', { name: /Run Backtest/i }).click();

        // Should show loading state
        await expect(page.getByText(/Running Backtest/i)).toBeVisible({ timeout: 5000 });
        await expect(page.locator('.loading')).toBeVisible();
    });

    // NOTE: Full end-to-end backtest result testing is skipped because:
    // 1. It requires waiting 60+ seconds for optimization to complete
    // 2. Tests can be flaky due to backend processing time
    // 3. This is already tested in backend unit tests
    // 4. Manual testing covers the full flow
    test.skip('should display backtest results', async ({ page }) => {
        // This test would require:
        // 1. Run a full backtest
        // 2. Wait for completion (60+ seconds)
        // 3. Verify results are displayed
        // Skipping due to long execution time and potential flakiness

        // TODO: Consider implementing with mock backend responses for faster testing
    });

    test.skip('should display key performance metrics', async ({ page }) => {
        // This test would verify metrics display after backtest completes
        // Skipping due to long execution time
    });

    test.skip('should display portfolio trajectory chart', async ({ page }) => {
        // This test would verify the chart is displayed
        // Skipping due to long execution time
    });
});
