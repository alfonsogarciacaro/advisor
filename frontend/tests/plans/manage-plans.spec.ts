
import { test, expect } from '@playwright/test';
import { createPlan, deletePlan } from '../test-utils';

test.describe('Plans - Manage Plans', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
    });

    test('should create multiple plans and switch between them', async ({ page }) => {
        // Use unique names per test
        const plan1 = `Retirement ${Date.now()}`;
        const plan2 = `Education ${Date.now()}`;

        // Create Plan 1
        await createPlan(page, plan1);
        await expect(page.locator('h1', { hasText: plan1 })).toBeVisible();

        // Go back
        await page.getByRole('button', { name: 'Back to Plans' }).click();

        // Create Plan 2
        await createPlan(page, plan2);
        await expect(page.locator('h1', { hasText: plan2 })).toBeVisible();

        // Go back
        await page.getByRole('button', { name: 'Back to Plans' }).click();

        // Expect both to be visible in list
        await expect(page.getByText(plan1)).toBeVisible();
        await expect(page.getByText(plan2)).toBeVisible();

        // Click Plan 1 to switch
        await page.getByText(plan1).click();
        await expect(page.locator('h1', { hasText: plan1 })).toBeVisible();
    });

    test('should delete a plan', async ({ page }) => {
        // Create unique plan for deletion test
        const planToDelete = `Delete Me ${Date.now()}`;
        await createPlan(page, planToDelete);

        // Go back to list
        await page.getByRole('button', { name: 'Back to Plans' }).click();

        // Delete it
        await deletePlan(page, planToDelete);

        // Verify it's gone
        await expect(page.getByText(planToDelete)).not.toBeVisible();
    });
});
