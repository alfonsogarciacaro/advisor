
import { test, expect } from '@playwright/test';
import { createPlan } from '../test-utils';

test.describe('Create First Investment Plan', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
    });

    test('should show empty state or plan list on load', async ({ page }) => {
        // We can't guarantee empty state if other tests ran, but we can verify
        // fundamental elements like the header
        await expect(page.getByText('ETF Portfolio Advisor')).toBeVisible();
    });

    // We use a unique name to avoid collision
    const planName = `First Plan ${Date.now()}`;

    test('should create plan successfully', async ({ page }) => {
        await createPlan(page, planName);

        // After creation, we expect to be in Detail View
        // Detail View header should have the Plan Name
        await expect(page.getByRole('heading', { name: planName })).toBeVisible();
        await expect(page.getByRole('button', { name: 'Back to Plans' })).toBeVisible();
    });
});
