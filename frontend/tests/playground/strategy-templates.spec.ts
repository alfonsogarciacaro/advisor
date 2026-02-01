import { test, expect } from '@playwright/test';
import { createPlan } from '../test-utils';

/**
 * PLAYGROUND FEATURE TESTS - STRATEGY TEMPLATES
 * 
 * Tests the strategy template selector in the Historical Audit feature.
 */

test.describe('Strategy Templates', () => {
    test.beforeEach(async ({ page }) => {
        // Create a unique plan for each test (avoid "Strategy" in name to prevent conflicts)
        const planName = `Test Strategy Plan ${Date.now()}`;
        await createPlan(page, planName);

        // Navigate to Playground tab
        await page.getByRole('tab', { name: 'Playground' }).click();

        // Wait for strategies to load
        await page.waitForSelector('select:not([disabled])', { timeout: 10000 });
        await page.waitForTimeout(500);
    });

    test('should display strategy template selector', async ({ page }) => {
        // Should show strategy template dropdown label
        await expect(page.getByText(/Strategy Template.*Optional/i)).toBeVisible();
        // Look for the select element
        await expect(page.locator('select')).toBeVisible();
    });

    test('should allow selecting "None" for custom constraints', async ({ page }) => {
        // Default should be "Custom Constraints (None)"
        const selectElement = page.locator('select');
        const value = await selectElement.inputValue();
        expect(value).toBe('');
    });

    test('should load and display available strategies', async ({ page }) => {
        // Click the select dropdown to see options
        await page.locator('select').click();

        // Should see several strategy options
        await expect(page.getByRole('option', { name: /Conservative Income/i })).toBeVisible();
        await expect(page.getByRole('option', { name: /Balanced Diversifier/i })).toBeVisible();
        await expect(page.getByRole('option', { name: /Aggressive Growth/i })).toBeVisible();
    });

    test('should show strategy details after selection', async ({ page }) => {
        // Select a strategy by finding its value (strategy_id)
        const selectElement = page.locator('select');
        // Get all options and find the one with Conservative Income
        const options = await selectElement.locator('option').allTextContents();
        const conservativeOption = options.find(o => o.includes('Conservative Income'));

        // Select by index or by exact text matching
        await selectElement.selectOption({ index: options.indexOf(conservativeOption!) });

        // Should show info with "Selected:" and strategy name
        await expect(page.getByText(/Selected: Conservative Income/i)).toBeVisible({ timeout: 3000 });
    });

    test('should allow selecting different strategies', async ({ page }) => {
        const selectElement = page.locator('select');
        const options = await selectElement.locator('option').allTextContents();

        // Select Conservative Income
        const conservativeIndex = options.findIndex(o => o.includes('Conservative Income'));
        await selectElement.selectOption({ index: conservativeIndex });
        await expect(page.getByText(/Selected: Conservative Income/i)).toBeVisible();

        // Change to Aggressive Growth
        const aggressiveIndex = options.findIndex(o => o.includes('Aggressive Growth'));
        await selectElement.selectOption({ index: aggressiveIndex });
        await expect(page.getByText(/Selected: Aggressive Growth/i)).toBeVisible();
    });

    test('should show risk level for selected strategy', async ({ page }) => {
        const selectElement = page.locator('select');
        const options = await selectElement.locator('option').allTextContents();
        const conservativeIndex = options.findIndex(o => o.includes('Conservative Income'));

        await selectElement.selectOption({ index: conservativeIndex });

        // Should show risk level information
        await expect(page.getByText(/Risk Level/i)).toBeVisible();
        // Should show the badge with risk level
        await expect(page.locator('.badge').filter({ hasText: /conservative/i })).toBeVisible();
    });

    test('should allow clearing strategy selection', async ({ page }) => {
        const selectElement = page.locator('select');
        const options = await selectElement.locator('option').allTextContents();

        // Select a strategy
        const balancedIndex = options.findIndex(o => o.includes('Balanced Diversifier'));
        await selectElement.selectOption({ index: balancedIndex });
        await expect(page.getByText(/Selected: Balanced Diversifier/i)).toBeVisible();

        // Clear selection by selecting first option (None)
        await selectElement.selectOption({ index: 0 });

        // Strategy info should be hidden
        await expect(page.getByText(/Selected: Balanced Diversifier/i)).not.toBeVisible();
    });

    // NOTE: Full E2E test with actual backtest using strategy is skipped
    // because it requires waiting 60+ seconds for optimization
    test.skip('should use strategy template for fear test', async ({ page }) => {
        // This would require:
        // 1. Select a strategy
        // 2. Run fear test
        // 3. Wait 60+ seconds
        // 4. Verify results respect strategy constraints
        // Skipping due to long execution time
    });

    test('should show strategies with different risk levels', async ({ page }) => {
        // Open the dropdown
        await page.locator('select').click();

        // Should have strategies with different risk levels (they appear in the option text)
        const selectText = await page.locator('select').textContent();
        expect(selectText).toMatch(/conservative/i);
        expect(selectText).toMatch(/moderate/i);
        expect(selectText).toMatch(/aggressive/i);
    });
});
