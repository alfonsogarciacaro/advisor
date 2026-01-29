
import { test, expect } from '@playwright/test';
import { createPlan } from '../test-utils';

test.describe('Optimization - Flow', () => {
    test.beforeEach(async ({ page }) => {
        // Create a unique plan for each test
        const planName = `Opt Flow Plan ${Date.now()}`;
        await createPlan(page, planName);

        // Wait for page to stabilize
        await page.waitForTimeout(1000);
    });

    test('should run optimization and display results', async ({ page }) => {
        // Verify optimizer form is visible
        const optimizeBtn = page.getByRole('button', { name: 'Optimize Portfolio' });
        await expect(optimizeBtn).toBeVisible();

        // Change amount to 20000 (default 10000)
        await page.getByLabel('Investment Amount').fill('20000');

        // Click Optimize
        await optimizeBtn.click();

        // Should see loading state
        await expect(page.getByText('Optimizing...')).toBeVisible();

        // Wait for COMPLETED status badge
        await expect(page.getByText('COMPLETED')).toBeVisible({ timeout: 60000 });

        // Verify Key Metrics are shown
        await expect(page.getByText('Initial Investment')).toBeVisible();
        await expect(page.getByText('Expected Annual Return')).toBeVisible();
        // Sharpe Ratio appears in both stats and table, use stat-title to target the stats section
        await expect(page.locator('.stat-title', { hasText: 'Sharpe Ratio' })).toBeVisible();

        // Verify scenarios section exists (use heading to avoid legend strict mode violation)
        await expect(page.getByRole('heading', { name: 'Base Case' })).toBeVisible();
        await expect(page.getByRole('heading', { name: 'Bull Case' })).toBeVisible();
        await expect(page.getByRole('heading', { name: 'Bear Case' })).toBeVisible();
    });
});
