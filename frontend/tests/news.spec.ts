import { test, expect } from '@playwright/test';

test('As a user I expect to see the latest financial news when opening the app', async ({ page }) => {
    // Go to the home page
    await page.goto('/');

    // Check if the "Latest Financial News" heading is visible
    const heading = page.getByRole('heading', { name: 'Latest Financial News' });
    await expect(heading).toBeVisible();

    // Check if the "Updated every 12h" badge is visible
    const badge = page.getByText('Updated every 12h');
    await expect(badge).toBeVisible();

    // Wait for the news items to load (they might be loading initially)
    // We expect at least one news item link
    // The component renders <a> tags with class containing "group relative block"
    // But a better selector would be based on the structure or mock data.
    // Since we are running against the real backend (or mocked backend if we chose to mock in playwright),
    // we should check for the presence of the grid.

    // Wait for the loading skeleton to disappear and news to appear
    // The loading state has "animate-pulse", the news items are in a grid.

    // We can look for the article titles. 
    // Since we don't know the exact news content, we can check if there is at least one article.

    // Locate the container that holds the heading "Latest Financial News"
    // The component structure is:
    // <div class="w-full space-y-6">
    //   <div><h2>...</h2></div>
    //   <div class="grid ...">...</div>
    // </div>
    // We can filter for the container div that has the heading.
    const newsContainer = page.locator('div.w-full.space-y-6').filter({ has: heading });
    await expect(newsContainer).toBeVisible();

    // Now find the grid within that container
    const newsGrid = newsContainer.locator('.grid');
    await expect(newsGrid).toBeVisible();

    // Check that we have at least one news card (anchor tag) inside the grid
    const newsCards = newsGrid.locator('a');
    await expect(newsCards.first()).toBeVisible();

    // Optional: Take a screenshot for debugging/verification
    await page.screenshot({ path: 'playwright-report/news-dashboard.png' });
});
