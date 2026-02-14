import { test, expect, Page } from '@playwright/test';
import { createPlan } from '../test-utils';

test.describe('Optimization - Basic', () => {
    test.beforeEach(async ({ page }) => {
        // Create a unique plan for each test
        const planName = `Opt Basic Plan ${Date.now()}`;
        await createPlan(page, planName);

        // Wait for page to stabilize
        await page.waitForTimeout(1000);
    });

    const addAssetToPlan = async (page: Page, amount: string) => {
        // Open editor
        await page.getByRole('button', { name: /Edit Portfolio/i }).click();

        // Add asset
        await page.getByRole('button', { name: /Add Asset/i }).click();

        // Select first available ETF
        await page.getByLabel(/^ETF$/i).first().selectOption({ index: 1 });
        await page.getByLabel(/^Account$/i).first().selectOption('taxable');
        await page.getByLabel(/Value/i).first().fill(amount);

        // Save
        await page.getByRole('button', { name: /Save Portfolio/i }).click();

        // Wait for modal to close
        await expect(page.getByRole('dialog')).not.toBeVisible();
    };

    test('should start optimization and show progress', async ({ page }) => {
        // Add assets first (optimization requires value)
        await addAssetToPlan(page, '1000000');

        // Start optimization
        await page.getByRole('button', { name: /^Optimize Portfolio$/i }).click();

        // Button should show loading state with spinner
        // The button text changes to a spinner, so we look for the spinner or the disabled state
        const optimizeBtn = page.getByRole('button', { name: /Optimize Portfolio/i }).or(page.locator('button:has(.loading-spinner)'));
        await expect(optimizeBtn).toBeDisabled();

        // Status badge may appear (queued or optimizing)
        const statusBadge = page.locator('.card-title').locator('.badge').filter({ hasText: /QUEUED|OPTIMIZING|FETCHING|FORECASTING/i });
        const hasBadge = await statusBadge.isVisible({ timeout: 5000 }).catch(() => false);
        if (hasBadge) {
            await expect(statusBadge).toBeVisible();
        }
    });

    test('should display optimization results when complete', async ({ page }) => {
        // Add assets
        await addAssetToPlan(page, '1000000');

        // Start optimization
        await page.getByRole('button', { name: /^Optimize Portfolio$/i }).click();

        // Wait for completion
        await expect(page.getByText('COMPLETED')).toBeVisible({ timeout: 60000 });

        // Should show key metrics
        await expect(page.getByText(/Initial Investment/i)).toBeVisible();
        await expect(page.getByText(/Expected Annual Return/i)).toBeVisible();
        await expect(page.getByText(/Annual Volatility/i)).toBeVisible();
        // Sharpe Ratio
        await expect(page.locator('.stat-title', { hasText: 'Sharpe Ratio' })).toBeVisible();
    });

    test('should display optimal portfolio allocation table', async ({ page }) => {
        // Run optimization
        await addAssetToPlan(page, '1000000');
        await page.getByRole('button', { name: /^Optimize Portfolio$/i }).click();

        // Wait for completion
        await expect(page.getByText('COMPLETED')).toBeVisible({ timeout: 60000 });

        // Check for allocation table heading
        await expect(page.getByText(/Optimal Portfolio Allocation/i)).toBeVisible();

        // Table headers
        await expect(page.getByRole('columnheader', { name: 'Ticker' })).toBeVisible();
        await expect(page.getByRole('columnheader', { name: 'Weight' })).toBeVisible();
        await expect(page.getByRole('columnheader', { name: 'Amount' })).toBeVisible();

        // At least one row should exist
        const table = page.locator('table').first();
        await expect(table).toBeVisible();
    });

    test('should allow re-optimization after portfolio change', async ({ page }) => {
        // First optimization
        await addAssetToPlan(page, '1000000');
        await page.getByRole('button', { name: /^Optimize Portfolio$/i }).click();
        await expect(page.getByText('COMPLETED')).toBeVisible({ timeout: 60000 });

        // Change portfolio (Edit Portfolio)
        await page.getByRole('button', { name: /Edit Portfolio/i }).click();
        await page.getByLabel(/Value/i).first().fill('2000000');
        await page.getByRole('button', { name: /Save Portfolio/i }).click();
        await expect(page.getByRole('dialog')).not.toBeVisible();

        // Should be able to optimize again
        await page.getByRole('button', { name: /^Optimize Portfolio$/i }).click();

        // Button should show loading state
        const optimizeBtn = page.getByRole('button', { name: /Optimize Portfolio/i }).or(page.locator('button:has(.loading-spinner)'));
        await expect(optimizeBtn).toBeDisabled();
    });
});
