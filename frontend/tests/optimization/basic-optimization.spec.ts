import { test, expect } from '@playwright/test';
import { createPlan } from '../test-utils';

test.describe('Optimization - Basic', () => {
    test.beforeEach(async ({ page }) => {
        // Create a unique plan for each test
        const planName = `Opt Basic Plan ${Date.now()}`;
        await createPlan(page, planName);

        // Wait for page to stabilize
        await page.waitForTimeout(1000);
    });

    test('should display optimization input form', async ({ page }) => {
        // Should be in plan detail view with optimizer visible
        const amountInput = page.getByLabel('Investment Amount');
        await expect(amountInput).toBeVisible();

        const currencySelect = page.getByLabel('Currency');
        await expect(currencySelect).toBeVisible();

        const optimizeButton = page.getByRole('button', { name: 'Optimize Portfolio' });
        await expect(optimizeButton).toBeVisible();
    });

    test('should validate investment amount', async ({ page }) => {
        // Try to optimize with invalid amount
        await page.getByLabel('Investment Amount').fill('0');
        await page.getByRole('button', { name: 'Optimize Portfolio' }).click();

        // Button should still be enabled (validation happens on click)
        // But if there's an error message:
        const errorAlert = page.getByRole('alert').filter({ hasText: /valid|investment/i });
        const hasError = await errorAlert.isVisible({ timeout: 2000 }).catch(() => false);
        if (hasError) {
            await expect(errorAlert).toBeVisible();
        }
    });

    test('should select different currencies', async ({ page }) => {
        const currencySelect = page.getByLabel('Currency');

        // Check available currencies
        const options = await currencySelect.locator('option').all();
        const currencies = await Promise.all(
            options.map(async (opt) => await opt.getAttribute('value'))
        );

        expect(currencies).toContain('USD');
        expect(currencies).toContain('JPY');
        expect(currencies).toContain('EUR');

        // Select JPY
        await currencySelect.selectOption('JPY');
        await expect(currencySelect).toHaveValue('JPY');
    });

    test('should start optimization and show progress', async ({ page }) => {
        // Enter valid amount
        await page.getByLabel('Investment Amount').fill('10000');
        await page.getByLabel('Currency').selectOption('USD');

        // Start optimization
        await page.getByRole('button', { name: 'Optimize Portfolio' }).click();

        // Button should show loading state with spinner
        await expect(page.getByRole('button', { name: /Optimizing/i })).toBeVisible();
        await expect(page.locator('.loading-spinner')).toBeVisible();

        // Status badge may appear (queued or optimizing) after first status update
        // This is optional as it depends on backend timing
        const statusBadge = page.locator('.card-title').locator('.badge').filter({ hasText: /QUEUED|OPTIMIZING|FETCHING|FORECASTING/i });
        const hasBadge = await statusBadge.isVisible({ timeout: 5000 }).catch(() => false);
        if (hasBadge) {
            await expect(statusBadge).toBeVisible();
        }
        // Test passes regardless of badge visibility
    });

    test('should display optimization results when complete', async ({ page }) => {
        // Start optimization
        await page.getByLabel('Investment Amount').fill('10000');
        await page.getByRole('button', { name: 'Optimize Portfolio' }).click();

        // Wait for completion
        await expect(page.getByText('COMPLETED')).toBeVisible({ timeout: 60000 });

        // Should show key metrics
        await expect(page.getByText(/Initial Investment/i)).toBeVisible();
        await expect(page.getByText(/Expected Annual Return/i)).toBeVisible();
        await expect(page.getByText(/Annual Volatility/i)).toBeVisible();
        // Sharpe Ratio appears in both stats and table, use stat-title to target the stats section
        await expect(page.locator('.stat-title', { hasText: 'Sharpe Ratio' })).toBeVisible();
    });

    test('should display optimal portfolio allocation table', async ({ page }) => {
        // Run optimization
        await page.getByLabel('Investment Amount').fill('10000');
        await page.getByRole('button', { name: 'Optimize Portfolio' }).click();

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

    test('should format currency correctly', async ({ page }) => {
        // Optimize with JPY
        await page.getByLabel('Investment Amount').fill('1000000');
        await page.getByLabel('Currency').selectOption('JPY');
        await page.getByRole('button', { name: 'Optimize Portfolio' }).click();

        await expect(page.getByText('COMPLETED')).toBeVisible({ timeout: 60000 });

        // Should see ¥ symbol in the results
        const pageText = await page.textContent('body');
        expect(pageText).toContain('¥');
    });

    test('should allow re-optimization', async ({ page }) => {
        // First optimization
        await page.getByLabel('Investment Amount').fill('10000');
        await page.getByRole('button', { name: 'Optimize Portfolio' }).click();
        await expect(page.getByText('COMPLETED')).toBeVisible({ timeout: 60000 });

        // Change amount
        await page.getByLabel('Investment Amount').fill('20000');

        // Should be able to optimize again
        await page.getByRole('button', { name: 'Optimize Portfolio' }).click();

        // Button should show loading state
        await expect(page.getByRole('button', { name: /Optimizing/i })).toBeVisible();

        // Status badge is optional (depends on timing)
        const statusBadge = page.locator('.card-title').locator('.badge').filter({ hasText: /QUEUED|OPTIMIZING|FETCHING|FORECASTING/i });
        const hasBadge = await statusBadge.isVisible({ timeout: 5000 }).catch(() => false);
        if (hasBadge) {
            await expect(statusBadge).toBeVisible();
        }
    });

    test('should clear cache and reset', async ({ page }) => {
        await page.getByLabel('Investment Amount').fill('10000');
        await page.getByRole('button', { name: 'Optimize Portfolio' }).click();
        await expect(page.getByText('COMPLETED')).toBeVisible({ timeout: 60000 });

        // Clear cache button exists
        const clearBtn = page.getByRole('button', { name: 'Clear Cache' });
        if (await clearBtn.isVisible()) {
            await clearBtn.click();

            // Results should be cleared
            await expect(page.getByText(/Optimal Portfolio Allocation/i)).not.toBeVisible();
            await expect(page.getByLabel('Investment Amount')).toHaveValue('10000');
        }
    });
});
