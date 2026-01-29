
import { test, expect } from '@playwright/test';
import { createPlan, deletePlan } from '../test-utils';

test.describe('Manage Plans', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
    });

    const plan1 = `Retirement ${Date.now()}`;
    const plan2 = `Education ${Date.now()}`;

    test('should create multiple plans and switch between them', async ({ page }) => {
        // Create Plan 1
        await createPlan(page, plan1);
        await expect(page.getByRole('heading', { name: plan1 })).toBeVisible();

        // Go back
        await page.getByRole('button', { name: 'Back to Plans' }).click();

        // Create Plan 2
        await createPlan(page, plan2);
        await expect(page.getByRole('heading', { name: plan2 })).toBeVisible();

        // Go back
        await page.getByRole('button', { name: 'Back to Plans' }).click();

        // Expect both to be visible in list
        // Use visible=true to ensure
        await expect(page.getByText(plan1)).toBeVisible();
        await expect(page.getByText(plan2)).toBeVisible();

        // Click Plan 1 to switch
        await page.getByText(plan1).click();
        await expect(page.getByRole('heading', { name: plan1 })).toBeVisible();
    });

    test('should delete a plan', async ({ page }) => {
        // Clean up plan1 if it exists or create new one for deletion test
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
