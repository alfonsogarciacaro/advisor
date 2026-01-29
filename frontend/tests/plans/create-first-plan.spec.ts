
import { test, expect } from '@playwright/test';
import { createPlan } from '../test-utils';

test.describe('Plans - Create First Plan', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
    });

    test('should show app header on load', async ({ page }) => {
        // Verify fundamental elements like the header
        await expect(page.getByText('ETF Portfolio Advisor')).toBeVisible();
    });

    test('should create plan successfully', async ({ page }) => {
        // Use a unique name to avoid collision
        const planName = `First Plan ${Date.now()}`;
        await createPlan(page, planName);

        // After creation, we expect to be in Detail View
        // Use h1 to avoid strict mode violation with ResearchPanel
        await expect(page.locator('h1', { hasText: planName })).toBeVisible();
        await expect(page.getByRole('button', { name: 'Back to Plans' })).toBeVisible();
    });
});
