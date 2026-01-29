import { test, expect } from '@playwright/test';

test.describe('Portfolio Optimization', () => {
    test.beforeEach(async ({ page }) => {
        // Navigate to plan detail view (assuming we have a plan)
        await page.goto('/');
        // For testing, we might need to create a plan first or mock it
        // This assumes a plan exists or we create one
    });

    test('should display optimization input form', async ({ page }) => {
        // Should be in plan detail view
        // Look for optimization form
        const amountInput = page.getByLabel(/Investment Amount/i);
        await expect(amountInput).toBeVisible();

        const currencySelect = page.getByLabel(/Currency/i);
        await expect(currencySelect).toBeVisible();

        const optimizeButton = page.getByRole('button', { name: /Optimize Portfolio/i });
        await expect(optimizeButton).toBeVisible();
    });

    test('should validate investment amount', async ({ page }) => {
        // Try to optimize with invalid amount
        await page.getByLabel(/Investment Amount/i).fill('0');
        await page.getByRole('button', { name: /Optimize Portfolio/i }).click();

        // Should show validation error
        await expect(page.getByText(/valid investment amount/i)).toBeVisible();
    });

    test('should select different currencies', async ({ page }) => {
        const currencySelect = page.getByLabel(/Currency/i);

        // Check available currencies
        const options = await currencySelect.locator('option').all();
        const currencies = await Promise.all(
            options.map(async (opt) => await opt.getAttribute('value'))
        );

        expect(currencies).toContain('USD');
        expect(currencies).toContain('JPY');
        expect(currencies).toContain('EUR');

        // Select JPY
        await currencySelect.selectOption('JPY');
        await expect(currencySelect).toHaveValue('JPY');
    });

    test('should start optimization and show progress', async ({ page }) => {
        // Enter valid amount
        await page.getByLabel(/Investment Amount/i).fill('10000');
        await page.getByLabel(/Currency/i).selectOption('USD');

        // Start optimization
        await page.getByRole('button', { name: /Optimize Portfolio/i }).click();

        // Button should show loading state
        await expect(page.getByRole('button', { name: /Optimizing/i })).toBeVisible();
        await expect(page.locator('.loading')).toBeVisible();

        // Status badge should appear
        await expect(page.getByText(/QUEUED/i)).toBeVisible();
    });

    test('should display optimization results when complete', async ({ page }) => {
        // Start optimization
        await page.getByLabel(/Investment Amount/i).fill('10000');
        await page.getByRole('button', { name: /Optimize Portfolio/i }).click();

        // Wait for completion (might need to increase timeout for real optimization)
        // For testing with mocks, this should be fast
        await expect(page.getByText(/COMPLETED/i), { timeout: 30000 }).toBeVisible();

        // Should show key metrics
        await expect(page.getByText(/Initial Investment/i)).toBeVisible();
        await expect(page.getByText(/Net Investment/i)).toBeVisible();
        await expect(page.getByText(/Expected Annual Return/i)).toBeVisible();
        await expect(page.getByText(/Annual Volatility/i)).toBeVisible();
        await expect(page.getByText(/Sharpe Ratio/i)).toBeVisible();
    });

    test('should display optimal portfolio allocation table', async ({ page }) => {
        // Run optimization first (or use mock data)
        await page.getByLabel(/Investment Amount/i).fill('10000');
        await page.getByRole('button', { name: /Optimize Portfolio/i }).click();

        // Wait for completion
        await expect(page.getByText(/COMPLETED/i), { timeout: 30000 }).toBeVisible();

        // Check for allocation table
        await expect(page.getByText(/Optimal Portfolio Allocation/i)).toBeVisible();

        // Table headers
        await expect(page.getByRole('columnheader', { name: 'Ticker' })).toBeVisible();
        await expect(page.getByRole('columnheader', { name: 'Weight' })).toBeVisible();
        await expect(page.getByRole('columnheader', { name: 'Amount' })).toBeVisible();
        await expect(page.getByRole('columnheader', { name: 'Shares' })).toBeVisible();
        await expect(page.getByRole('columnheader', { name: 'Price' })).toBeVisible();
        await expect(page.getByRole('columnheader', { name: 'Expected Return' })).toBeVisible();

        // At least one row should exist
        const rows = page.getByRole('row').filter({ hasText: /^[A-Z]+/ }); // Has ticker symbol
        await expect(rows.first()).toBeVisible();
    });

    test('should format currency correctly', async ({ page }) => {
        // Optimize with JPY
        await page.getByLabel(/Investment Amount/i).fill('1000000');
        await page.getByLabel(/Currency/i).selectOption('JPY');
        await page.getByRole('button', { name: /Optimize Portfolio/i }).click();

        await expect(page.getByText(/COMPLETED/i), { timeout: 30000 }).toBeVisible();

        // Should see ¥ symbol
        await expect(page.getByText(/¥/)).toBeVisible();
    });

    test('should show efficient frontier chart', async ({ page }) => {
        await page.getByLabel(/Investment Amount/i).fill('10000');
        await page.getByRole('button', { name: /Optimize Portfolio/i }).click();

        await expect(page.getByText(/COMPLETED/i), { timeout: 30000 }).toBeVisible();

        // Chart should be visible
        await expect(page.getByText(/Efficient Frontier/i)).toBeVisible();

        // Check for chart container (ResponsiveContainer from Recharts)
        await expect(page.locator('.recharts-wrapper').or(page.locator('.responsive-container'))).toBeVisible();
    });

    test('should display scenario forecasts', async ({ page }) => {
        await page.getByLabel(/Investment Amount/i).fill('10000');
        await page.getByRole('button', { name: /Optimize Portfolio/i }).click();

        await expect(page.getByText(/COMPLETED/i), { timeout: 30000 }).toBeVisible();

        // Should see scenarios section
        await expect(page.getByText(/Scenario Forecasts/i)).toBeVisible();

        // Should have Base, Bull, and Bear cases
        await expect(page.getByText(/Base Case/i)).toBeVisible();
        await expect(page.getByText(/Bull Case/i)).toBeVisible();
        await expect(page.getByText(/Bear Case/i)).toBeVisible();

        // Each scenario should have probability badge
        const probabilityBadges = page.getByRole('button', { name: /probability/i });
        await expect(probabilityBadges).toHaveCount(3);
    });

    test('should show AI analysis report', async ({ page }) => {
        await page.getByLabel(/Investment Amount/i).fill('10000');
        await page.getByRole('button', { name: /Optimize Portfolio/i }).click();

        // Wait for generating_analysis phase
        await expect(page.getByText(/generating_analysis/i), { timeout: 30000 }).toBeVisible();

        // Eventually should show completed report
        await expect(page.getByText(/AI Analysis Report/i), { timeout: 60000 }).toBeVisible();

        // Report should have content (markdown rendered)
        const reportSection = page.locator('.prose').or(page.locator('.markdown'));
        await expect(reportSection).toBeVisible();
    });

    test('should allow re-optimization', async ({ page }) => {
        // First optimization
        await page.getByLabel(/Investment Amount/i).fill('10000');
        await page.getByRole('button', { name: /Optimize Portfolio/i }).click();
        await expect(page.getByText(/COMPLETED/i), { timeout: 30000 }).toBeVisible();

        // Change amount
        await page.getByLabel(/Investment Amount/i).fill('20000');

        // Should be able to optimize again
        await page.getByRole('button', { name: /Optimize Portfolio/i }).click();
        await expect(page.getByText(/QUEUED/i)).toBeVisible();
    });

    test('should clear cache and reset', async ({ page }) => {
        await page.getByLabel(/Investment Amount/i).fill('10000');
        await page.getByRole('button', { name: /Optimize Portfolio/i }).click();
        await expect(page.getByText(/COMPLETED/i), { timeout: 30000 }).toBeVisible();

        // Clear cache
        await page.getByRole('button', { name: /Clear Cache/i }).click();

        // Results should be cleared
        await expect(page.getByText(/Optimal Portfolio Allocation/i)).not.toBeVisible();
        await expect(page.getByLabel(/Investment Amount/i)).toHaveValue('10000');
    });
});
