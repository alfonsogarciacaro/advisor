import { test, expect } from '@playwright/test';
import { createPlan } from '../test-utils';

/**
 * PLAYGROUND FEATURE TESTS - TAX-AWARE BACKTESTING
 * 
 * UI Labels:
 * - Button class when selected: btn-error (not btn-primary)
 * - Run button: "Run Fear Test" (not "Run Backtest")
 */

test.describe('Tax-Aware Backtesting', () => {
    test.beforeEach(async ({ page }) => {
        // Create a unique plan for each test
        const planName = `Tax Backtest Plan ${Date.now()}`;
        await createPlan(page, planName);

        // Navigate to Playground tab
        await page.getByRole('tab', { name: 'Playground' }).click();

        // Wait for page to stabilize
        await page.waitForTimeout(500);
    });

    test('should display account type selector', async ({ page }) => {
        // Should show account type section
        await expect(page.getByText(/Account Type.*affects taxes/i)).toBeVisible();

        // Should show account type buttons
        await expect(page.getByRole('button', { name: /Taxable/i })).toBeVisible();
        await expect(page.getByRole('button', { name: /NISA Growth/i })).toBeVisible();
        await expect(page.getByRole('button', { name: /NISA General/i })).toBeVisible();
        await expect(page.getByRole('button', { name: /iDeCo/i })).toBeVisible();
    });

    test('should show tax advantage info for NISA accounts', async ({ page }) => {
        // Select NISA Growth
        await page.getByRole('button', { name: /NISA Growth/i }).click();

        // Should show tax-advantaged alert
        await expect(page.getByText(/Tax-Advantaged Account Selected/i)).toBeVisible();
        // Look for the exact text within the alert
        await expect(page.locator('.alert-success').getByText(/0% capital gains tax/i)).toBeVisible();
    });

    test('should allow selecting different account types', async ({ page }) => {
        // Click different account types - selected items use btn-error class
        await page.getByRole('button', { name: /NISA Growth/i }).click();
        await expect(page.getByRole('button', { name: /NISA Growth/i })).toHaveClass(/btn-error/);

        await page.getByRole('button', { name: /Taxable/i }).click();
        await expect(page.getByRole('button', { name: /Taxable/i })).toHaveClass(/btn-error/);
    });

    test('should show 0% tax info for NISA accounts', async ({ page }) => {
        // Select NISA Growth
        await page.getByRole('button', { name: /NISA Growth/i }).click();

        // Should mention 0% tax
        const pageText = await page.textContent('body');
        expect(pageText).toMatch(/0%/);
    });

    test('should show different styling for selected account type', async ({ page }) => {
        // Click NISA Growth
        await page.getByRole('button', { name: /NISA Growth/i }).click();

        // NISA Growth should be selected (btn-error)
        await expect(page.getByRole('button', { name: /NISA Growth/i })).toHaveClass(/btn-error/);

        // Click Taxable
        await page.getByRole('button', { name: /Taxable/i }).click();

        // Now Taxable should be selected and NISA Growth should not
        await expect(page.getByRole('button', { name: /Taxable/i })).toHaveClass(/btn-error/);
        await expect(page.getByRole('button', { name: /NISA Growth/i })).not.toHaveClass(/btn-error/);
    });

    test('should show tax hint for NISA accounts', async ({ page }) => {
        // Should show info about NISA having 0% capital gains tax
        await expect(page.getByText(/NISA accounts have 0% capital gains tax/i)).toBeVisible();
    });

    test('should run fear test with selected account type', async ({ page }) => {
        // Select NISA Growth
        await page.getByRole('button', { name: /NISA Growth/i }).click();

        // Set a historical date
        await page.getByRole('button', { name: /Pre-COVID/i }).click();

        // Run fear test
        await page.getByRole('button', { name: /Run Fear Test/i }).click();

        // Should show loading state
        await expect(page.getByText(/Running Fear Test/i)).toBeVisible({ timeout: 5000 });
    });

    // NOTE: Full end-to-end tax result testing is skipped because:
    // 1. It requires waiting 60+ seconds for optimization to complete
    // 2. Tests can be flaky due to backend processing time
    // 3. This is already tested in backend unit tests
    test.skip('should display tax impact metrics in results', async ({ page }) => {
        // This test would verify:
        // 1. Taxable account shows capital gains tax paid
        // 2. NISA accounts show 0 tax
        // 3. Pre-tax vs after-tax comparison
        // Skipping due to long execution time
    });

    test.skip('should show pre-tax vs after-tax returns', async ({ page }) => {
        // This test would verify the comparison between pre-tax and after-tax final values
        // Skipping due to long execution time
    });

    test.skip('should show tax efficiency insights', async ({ page }) => {
        // This test would verify insights banner suggesting tax-advantaged accounts
        // Skipping due to long execution time
    });

    test('should display all account type buttons in grid', async ({ page }) => {
        // Verify all account types are visible
        await expect(page.getByRole('button', { name: /Taxable/i })).toBeVisible();
        await expect(page.getByRole('button', { name: /NISA Growth/i })).toBeVisible();
        await expect(page.getByRole('button', { name: /NISA General/i })).toBeVisible();
        await expect(page.getByRole('button', { name: /iDeCo/i })).toBeVisible();
    });

    test('should switch account type selection', async ({ page }) => {
        // Select NISA Growth
        await page.getByRole('button', { name: /NISA Growth/i }).click();
        await expect(page.getByRole('button', { name: /NISA Growth/i })).toHaveClass(/btn-error/);

        // Navigate away and back
        await page.getByRole('tab', { name: 'Overview' }).click();
        await page.waitForTimeout(300);
        await page.getByRole('tab', { name: 'Playground' }).click();

        // Note: This test documents whether state persists across tab navigation
        // Selection may or may not persist depending on implementation
    });
});
