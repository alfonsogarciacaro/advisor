import { test, expect } from '@playwright/test';

test.describe('News - Display', () => {
    test('should show latest financial news', async ({ page }) => {
        // Go to the home page
        await page.goto('/');

        // Check if the "Latest Financial News" heading is visible
        const heading = page.getByRole('heading', { name: 'Latest Financial News' });
        await expect(heading).toBeVisible();

        // Check if the "Updated every 12h" badge is visible
        const badge = page.getByText('Updated every 12h');
        await expect(badge).toBeVisible();

        // Locate the news container
        const newsContainer = page.locator('div.w-full.space-y-6').filter({ has: heading });
        await expect(newsContainer).toBeVisible();

        // Find the grid within that container
        const newsGrid = newsContainer.locator('.grid');
        await expect(newsGrid).toBeVisible();

        // Check that we have at least one news card inside the grid
        const newsCards = newsGrid.locator('a');
        await expect(newsCards.first()).toBeVisible();
    });
});
