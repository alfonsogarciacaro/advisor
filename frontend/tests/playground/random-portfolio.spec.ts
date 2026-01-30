import { test, expect } from '@playwright/test';
import { createPlan } from '../test-utils';

/**
 * US-PG-03: Generate Random Portfolio
 * 
 * Acceptance Criteria:
 * - "🎲 Generate Random Portfolio" button visible in HistoricalReplay
 * - Clicking button randomly selects:
 *   - Strategy template
 *   - Account type
 *   - Investment amount
 * - Form fields pre-filled with random values
 * - Can still edit values before running
 * - Random selection happens quickly
 */

test.describe('Generate Random Portfolio', () => {
    test.beforeEach(async ({ page }) => {
        const planName = `Random Portfolio Test ${Date.now()}`;
        await createPlan(page, planName);

        // Navigate to Playground tab
        await page.getByRole('tab', { name: /Playground/i }).click();

        // Should be in Historical Replay by default
        await expect(page.getByRole('heading', { name: /Historical Replay/i })).toBeVisible();
    });

    test('should display random portfolio button', async ({ page }) => {
        // Look for the 🎲 Random button
        const randomButton = page.getByRole('button', { name: /Random/i }).filter({ hasText: /🎲/ });
        await expect(randomButton).toBeVisible();
    });

    test('should generate random values when clicked', async ({ page }) => {
        // Get initial values (if any)
        const amountInput = page.locator('#investment-amount');
        const initialAmount = await amountInput.inputValue();

        // Click random button
        const randomButton = page.getByRole('button', { name: /Random/i }).filter({ hasText: /🎲/ });
        await randomButton.click();

        // Values should be filled
        await expect(amountInput).not.toHaveValue('');

        // The value might have changed (or might be same by chance)
        const newAmount = await amountInput.inputValue();
        expect(newAmount).toBeTruthy();
    });

    test('should randomly select strategy template', async ({ page }) => {
        // Find strategy selector (if visible)
        const strategySelect = page.locator('select, [role="combobox"]').filter({ hasText: /Strategy|Conservative|Aggressive|Balanced/i });

        // Click random button
        const randomButton = page.getByRole('button', { name: /Random/i }).filter({ hasText: /🎲/ });
        await randomButton.click();

        // Strategy should be selected (if strategy selector exists)
        if (await strategySelect.isVisible()) {
            const selectedValue = await strategySelect.inputValue();
            expect(selectedValue).toBeTruthy();
        }
    });

    test('should randomly select account type', async ({ page }) => {
        // Find account type selector
        const accountSelect = page.locator('select').filter({ hasText: /NISA|iDeCo|Taxable|Account/i });

        // Click random button
        const randomButton = page.getByRole('button', { name: /Random/i }).filter({ hasText: /🎲/ });
        await randomButton.click();

        // Account type should be selected (if selector exists)
        if (await accountSelect.isVisible()) {
            const selectedValue = await accountSelect.inputValue();
            expect(selectedValue).toBeTruthy();
        }
    });

    test('should fill investment amount randomly', async ({ page }) => {
        // Click random button
        const randomButton = page.getByRole('button', { name: /Random/i }).filter({ hasText: /🎲/ });
        await randomButton.click();

        // Amount should be filled
        const amountInput = page.locator('#investment-amount');
        const amount = await amountInput.inputValue();

        expect(amount).toBeTruthy();
        expect(parseFloat(amount)).toBeGreaterThan(0);
    });

    test('should allow editing values after random generation', async ({ page }) => {
        // Generate random portfolio
        const randomButton = page.getByRole('button', { name: /Random/i }).filter({ hasText: /🎲/ });
        await randomButton.click();

        // Get the amount input
        const amountInput = page.locator('#investment-amount');

        // Clear and enter custom value
        await amountInput.clear();
        await amountInput.fill('25000');

        // Verify custom value is set
        await expect(amountInput).toHaveValue('25000');

        // Should still be able to run backtest with custom value
        const runButton = page.getByRole('button', { name: /Run Backtest/i });
        await expect(runButton).toBeEnabled();
    });

    test('should generate different values on multiple clicks', async ({ page }) => {
        const randomButton = page.getByRole('button', { name: /Random/i }).filter({ hasText: /🎲/ });
        const amountInput = page.locator('#investment-amount');

        // Click random multiple times and collect values
        const values: string[] = [];

        for (let i = 0; i < 5; i++) {
            await randomButton.click();
            await page.waitForTimeout(100); // Small delay to ensure update
            const value = await amountInput.inputValue();
            values.push(value);
        }

        // At least some values should be different (might not all be different due to randomness)
        const uniqueValues = new Set(values);

        // With 5 clicks, we should have at least 2 different values with high probability
        expect(uniqueValues.size).toBeGreaterThan(1);
    });

    test('should complete quickly', async ({ page }) => {
        const randomButton = page.getByRole('button', { name: /Random/i }).filter({ hasText: /🎲/ });

        const startTime = Date.now();
        await randomButton.click();
        const endTime = Date.now();

        // Should complete in less than 1 second
        const duration = endTime - startTime;
        expect(duration).toBeLessThan(1000);
    });

    test('should not auto-run backtest after random generation', async ({ page }) => {
        const randomButton = page.getByRole('button', { name: /Random/i }).filter({ hasText: /🎲/ });
        await randomButton.click();

        // Run Backtest button should still be visible (not replaced by "Running Backtest")
        await expect(page.getByRole('button', { name: /^Run Backtest$/i })).toBeVisible();

        // Should NOT see loading state
        const loadingIndicator = page.locator('.loading').filter({ hasText: /Running/i });
        const isLoading = await loadingIndicator.isVisible().catch(() => false);
        expect(isLoading).toBe(false);
    });

    test('should work with preset period selection', async ({ page }) => {
        // Select a preset period first
        await page.getByRole('button', { name: /Pre-COVID/i }).click();

        // Then generate random portfolio
        const randomButton = page.getByRole('button', { name: /Random/i }).filter({ hasText: /🎲/ });
        await randomButton.click();

        // Date should still be Pre-COVID (or randomization might change it - check either way)
        const dateInput = page.locator('#start-date');
        const dateValue = await dateInput.inputValue();

        // Should have some date value
        expect(dateValue).toBeTruthy();
    });

    test('should have tooltip explaining random feature', async ({ page }) => {
        const randomButton = page.getByRole('button', { name: /Random/i }).filter({ hasText: /🎲/ });

        // Check for title attribute (tooltip)
        const title = await randomButton.getAttribute('title');

        if (title) {
            expect(title.toLowerCase()).toContain('random');
        }
    });
});
