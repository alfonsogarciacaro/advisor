
import { test, expect } from '@playwright/test';
import { createPlan } from '../test-utils';

test.describe('Optimization Flow', () => {
    const planName = `Opt Plan ${Date.now()}`;

    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await createPlan(page, planName);
    });

    test('should run optimization and display results', async ({ page }) => {
        // Verify we are in detail view and "Start Portfolio Optimization" or optimizer form is visible.
        // If no optimization exists, "Start Portfolio Optimization" card is visible with PortfolioOptimizer inside.

        // Check for Optimize button
        const optimizeBtn = page.getByRole('button', { name: 'Optimize Portfolio' });
        await expect(optimizeBtn).toBeVisible();

        // Change amount to 20000 (default 10000)
        await page.getByLabel('Investment Amount').fill('20000');

        // Click Optimize
        await optimizeBtn.click();

        // Should see loading state
        await expect(page.getByText('Optimizing...')).toBeVisible();

        // Wait for results
        // Badge should eventually be "COMPLETED" or "GENERATING ANALYSIS"
        // We can wait for "Efficient Frontier" heading which appears on completion
        await expect(page.getByRole('heading', { name: 'Efficient Frontier' })).toBeVisible({ timeout: 60000 }); // Increase timeout for reliable tests

        // Verify Key Metrics
        await expect(page.getByText('Expected Annual Return')).toBeVisible();
        await expect(page.getByText('Sharpe Ratio')).toBeVisible();

        // Verify Efficient Frontier Chart - looking for the legend text
        await expect(page.getByText('Efficient Frontier', { exact: true })).toBeVisible();

        // Verify Scenarios
        await expect(page.getByText('Scenario Forecasts')).toBeVisible();
        await expect(page.getByText('Bull Case')).toBeVisible();
        await expect(page.getByText('Bear Case')).toBeVisible();
    });
});
