
import { Page, expect } from '@playwright/test';

export const createPlan = async (page: Page, name: string) => {
    // If not already on home, go there
    if (page.url() === 'about:blank') {
        await page.goto('/');
    }

    // Click "New Plan" or "Create Your First Plan"
    // Use a broad selector that matches either
    const createButton = page.getByRole('button', { name: /create.*plan|new plan/i });
    if (await createButton.isVisible()) {
        await createButton.click();
    } else {
        // Maybe we are already in a plan? Check if Back button exists
        const backButton = page.getByRole('button', { name: 'Back to Plans' });
        if (await backButton.isVisible()) {
            await backButton.click();
            await createButton.click();
        }
    }

    // Wait for modal
    await expect(page.getByRole('dialog')).toBeVisible();

    // Fill form
    await page.getByLabel('Plan Name').fill(name);
    await page.getByLabel('Risk Preference').selectOption('moderate');

    // Submit
    await page.getByRole('button', { name: 'Create Plan' }).click();

    // Verify modal closed
    await expect(page.getByRole('dialog')).not.toBeVisible();

    // Verify plan is visible in list or detail view
    // Since creation selects the plan, we might be in detail view
    // Detail view has "Back to Plans" and the plan name in header
    // Use h1 selector to avoid matching the ResearchPanel's h2 which also contains the plan name
    await expect(page.locator('h1', { hasText: name })).toBeVisible();
};

export const deletePlan = async (page: Page, name: string) => {
    // Must be in list view
    const backButton = page.getByRole('button', { name: 'Back to Plans' });
    if (await backButton.isVisible()) {
        await backButton.click();
    }

    // Find plan card using aria-label
    const planCard = page.getByRole('button', { name: `Plan: ${name}` });

    // Click the delete button within the plan card
    page.on('dialog', dialog => dialog.accept()); // Handle confirmation
    await planCard.getByTitle('Delete plan').click();

    // Verify plan card is gone
    await expect(planCard).not.toBeVisible();
};
