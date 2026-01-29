
import { test, expect } from '@playwright/test';
import { createPlan } from '../test-utils';

test.describe('Research - Agent', () => {
    test.beforeEach(async ({ page }) => {
        // Create a unique plan for each test
        const planName = `Research Plan ${Date.now()}`;
        await createPlan(page, planName);
    });

    test('should display research panel', async ({ page }) => {
        // Research panel should be visible in plan detail view
        await expect(page.getByText(/Research Agent/i)).toBeVisible();

        // Should show custom question input
        const input = page.getByPlaceholder(/recession/);
        await expect(input).toBeVisible();
    });

    test('should ask custom research question', async ({ page }) => {
        // Find the input field
        const input = page.getByPlaceholder(/recession/);
        await expect(input).toBeVisible();

        // Ask question
        await input.fill('Is this portfolio safe for retirement?');

        // Click the submit button (has an arrow icon, no text)
        const submitBtn = input.locator('..').getByRole('button').first();
        await submitBtn.click();

        // Expect loading state (spinner)
        await expect(page.locator('.loading')).toBeVisible();

        // Wait for completion (research completed alert)
        await expect(page.getByText(/Research completed/i)).toBeVisible({ timeout: 60000 });

        // The run_id should be shown
        await expect(page.getByText(/Run ID:/i)).toBeVisible();

        // Summary section should be visible (use heading to avoid strict mode)
        await expect(page.getByRole('heading', { name: 'Summary' })).toBeVisible();
    });

    test('should submit question with Enter key', async ({ page }) => {
        const input = page.getByPlaceholder(/recession/);

        // Type question
        await input.fill('Test question for Enter key');

        // Press Enter
        await input.press('Enter');

        // Should trigger research
        await expect(page.locator('.loading')).toBeVisible();

        // Should eventually complete
        await expect(page.getByText(/Research completed/i)).toBeVisible({ timeout: 60000 });
    });

    test('should show error when question is empty', async ({ page }) => {
        const input = page.getByPlaceholder(/recession/);

        // Button should be disabled when input is empty
        const submitBtn = input.locator('..').getByRole('button').first();
        await expect(submitBtn).toBeDisabled();

        // Try to type and then clear to verify it becomes disabled again
        await input.fill('Test');
        await expect(submitBtn).toBeEnabled();

        await input.fill('');
        await expect(submitBtn).toBeDisabled();
    });
});
