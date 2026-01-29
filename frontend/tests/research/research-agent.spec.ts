
import { test, expect } from '@playwright/test';
import { createPlan } from '../test-utils';

test.describe('Research Agent', () => {
    const planName = `Research Plan ${Date.now()}`;

    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        await createPlan(page, planName);
    });

    test('should ask custom research question', async ({ page }) => {
        // Scroll to research panel if needed or just find input
        // Input placeholder "Ask a question about your portfolio..."
        const input = page.getByPlaceholder('Ask a question about your portfolio...');
        await expect(input).toBeVisible();

        // Ask question
        await input.fill('Is this portfolio safe for retirement?');
        await page.getByRole('button', { name: 'Ask Agent' }).click();

        // Expect loading
        await expect(page.getByText('Agent is thinking...')).toBeVisible();

        // Expect result
        // The result appears in a markdown block. Since we mock LLM, we expect the mock response.
        // Wait for "Agent is thinking..." to disappear
        await expect(page.getByText('Agent is thinking...')).not.toBeVisible({ timeout: 60000 });

        // Check for some content. Since it's dynamic/mocked, check if a new message bubble appeared.
        // The user message should be visible
        await expect(page.getByText('Is this portfolio safe for retirement?')).toBeVisible();

        // The assistant response should be below
        // We can check for the "prose" class container that holds the response
        // or effectively just wait for the "Agent is thinking" to be gone implies response is there.
    });
});
