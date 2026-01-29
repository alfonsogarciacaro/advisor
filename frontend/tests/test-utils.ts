
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
    await expect(page.getByRole('heading', { name: name })).toBeVisible();
};

export const deletePlan = async (page: Page, name: string) => {
    // Must be in list view
    const backButton = page.getByRole('button', { name: 'Back to Plans' });
    if (await backButton.isVisible()) {
        await backButton.click();
    }

    // Find plan card delete button
    // This is tricky because the delete button is icon-only and inside the card.
    // Structure: card -> card-body -> ... -> title="Delete plan"
    // We navigate to the card containing the name, then find the delete button.

    // Playwright locator strategy:
    // Locate the card wrapper that contains the text 'name'
    const planCard = page.locator('.card').filter({ hasText: name });

    // Hover over it to ensure visibility if needed (usually nice in tests)
    await planCard.hover();

    // Click cancel/delete button. The tooltip is "Delete plan"
    // Using title attribute locator
    page.on('dialog', dialog => dialog.accept()); // Handle confirmation
    await planCard.getByTitle('Delete plan').click();

    // Verify gone
    await expect(planCard).not.toBeVisible();
};
