
import { Page, expect } from '@playwright/test';

export const loginUser = async (page: Page) => {
    // Check if already logged in (UserMenu exists?)
    // Or check if Sign In button exists
    const signInBtn = page.getByRole('button', { name: 'Sign In' });

    // If we are not on a page with header, we might miss it. 
    // Usually createPlan ensures we are on home.

    if (await signInBtn.isVisible()) {
        await signInBtn.click();

        // Wait for modal
        await expect(page.getByRole('dialog')).toBeVisible();

        // Switch to Sign Up
        // "Don't have an account? Sign up" - "Sign up" is a button inside the text
        await page.getByRole('button', { name: 'Sign up' }).click();

        // Fill form
        const username = `testuser_${Date.now()}_${Math.floor(Math.random() * 1000)}`;
        await page.getByPlaceholder('Enter your username').fill(username);
        await page.getByPlaceholder('Enter your password').fill('password123');
        await page.getByPlaceholder('Confirm your password').fill('password123');

        // Submit
        await page.getByRole('button', { name: 'Create Account' }).click();

        // Wait for modal to close or Sign In button to disappear
        await expect(signInBtn).not.toBeVisible({ timeout: 15000 });
    }
};

export const createPlan = async (page: Page, name: string) => {
    // If not already on home, go there
    if (page.url() === 'about:blank') {
        await page.goto('/');
    }

    // Ensure we are logged in
    await loginUser(page);

    // Click "New Plan" or "Create Your First Plan"

    // Click "New Plan" or "Create Your First Plan"
    // Click "New Plan" or "Create Your First Plan"
    const firstPlanBtn = page.getByRole('button', { name: 'Create Your First Plan' });
    const newPlanBtn = page.getByRole('button', { name: 'New Plan' });

    if (await firstPlanBtn.isVisible()) {
        await firstPlanBtn.click();
    } else if (await newPlanBtn.isVisible()) {
        await newPlanBtn.click();
    } else {
        // Maybe we are already in a plan? Check if Back button exists
        const backButton = page.getByRole('button', { name: 'Back to Plans' });
        if (await backButton.isVisible()) {
            await backButton.click();
            if (await newPlanBtn.isVisible()) {
                await newPlanBtn.click();
            } else {
                await firstPlanBtn.click();
            }
        }
    }

    // Wait for modal
    await expect(page.getByRole('dialog')).toBeVisible();

    // Fill form
    await page.getByLabel('Plan Name').fill(name);
    await page.getByLabel('Risk Preference').selectOption('moderate');

    // Get the dialog before clicking submit (so we can wait for it to close)
    const createDialog = page.getByRole('dialog').filter({ has: page.getByText('Create Plan') });

    // Submit
    await page.getByRole('button', { name: 'Create Plan' }).click();

    // Wait for plan creation dialog to close specifically (not other modals like research panel)
    await expect(createDialog).not.toBeVisible({ timeout: 30000 });

    // Verify plan is visible in detail view
    // Detail view has "Back to Plans" and the plan name in header
    // Use h1 selector to avoid matching the ResearchPanel's h2 which also contains the plan name
    await expect(page.locator('h1', { hasText: name })).toBeVisible({ timeout: 10000 });

    // Wait a bit for plan detail to fully load (ETFs, accounts, etc.)
    await page.waitForTimeout(1000);
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
