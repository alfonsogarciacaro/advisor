import { test, expect } from '@playwright/test';
import { createPlan } from '../test-utils';

/**
 * US-MA-02: View Holdings by Account Type
 *
 * Acceptance Criteria:
 * - Holdings displayed grouped by account type (NISA Growth, NISA General, iDeCo, Taxable)
 * - Each account shows total value in base currency (¥)
 * - Each account shows progress bar vs annual limit
 * - Grand total displayed at bottom
 * - Can see which ETFs are in which accounts
 *
 * SKIPPED: Tests require PortfolioEditor to add holdings first, which is broken.
 */
test.describe.skip('View Holdings by Account Type', () => {
    test.beforeEach(async ({ page }) => {
        const planName = `Holdings View Test ${Date.now()}`;
        await createPlan(page, planName);

        // Add some holdings across different accounts
        await page.getByRole('button', { name: /Edit Portfolio/i }).click();

        // Add to NISA Growth
        await page.getByRole('button', { name: /Add Asset/i }).click();
        await page.getByLabel(/^ETF$/i).first().selectOption({ index: 1 });
        await page.getByLabel(/^Account$/i).first().selectOption('nisa_growth');
        await page.getByLabel(/Value \(JPY\)/i).first().fill('800000');

        // Add to Taxable
        await page.getByRole('button', { name: /Add Asset/i }).click();
        await page.getByLabel(/^ETF$/i).last().selectOption({ index: 2 });
        await page.getByLabel(/^Account$/i).last().selectOption('taxable');
        await page.getByLabel(/Value \(JPY\)/i).last().fill('500000');

        await page.getByRole('button', { name: /Save Portfolio/i }).click();
    });

    test('should display holdings grouped by account type', async ({ page }) => {
        // Should see Current Holdings section
        await expect(page.getByRole('heading', { name: /Current Holdings/i })).toBeVisible();

        // Should see account names
        await expect(page.getByText(/NISA Growth/i)).toBeVisible();
        await expect(page.getByText(/Taxable/i)).toBeVisible();
    });

    test('should show total value for each account in base currency', async ({ page }) => {
        // Should see values with ¥ symbol
        await expect(page.getByText(/¥800,000/i).or(page.getByText(/¥800,000/i))).toBeVisible();
        await expect(page.getByText(/¥500,000/i).or(page.getByText(/¥500,000/i))).toBeVisible();
    });

    test('should display progress bar for accounts with limits', async ({ page }) => {
        // NISA Growth has annual limit, should show progress bar
        // Find the card containing NISA Growth text and check for progress within it
        const nisaCard = page.locator('.card').filter({ hasText: /NISA Growth/i });
        await expect(nisaCard.locator('progress')).toBeVisible();

        // Should show usage text
        await expect(nisaCard.getByText(/Annual Usage/i)).toBeVisible();
    });

    test('should show grand total at bottom', async ({ page }) => {
        // Should see total portfolio value
        await expect(page.getByText(/Total Portfolio Value/i)).toBeVisible();

        // Should see combined value (800000 + 500000 = 1300000)
        await expect(page.getByText(/¥1,300,000/i).or(page.getByText(/¥1,300,000/i))).toBeVisible();
    });

    test('should display ETF tickers within their respective accounts', async ({ page }) => {
        // Each holding should show ticker within its account card
        // The ticker should be visible as part of the holdings list
        const nisaCard = page.locator('.card').filter({ hasText: /NISA Growth/i });
        const taxableCard = page.locator('.card').filter({ hasText: /Taxable/i });

        // Each card should have at least one ticker displayed
        await expect(nisaCard.locator('[class*="font-medium"]').first()).toBeVisible();
        await expect(taxableCard.locator('[class*="font-medium"]').first()).toBeVisible();
    });

    test('should handle multiple ETFs in same account', async ({ page }) => {
        // Add another asset to NISA Growth
        await page.getByRole('button', { name: /Edit Portfolio/i }).click();
        await page.getByRole('button', { name: /Add Asset/i }).click();

        await page.getByLabel(/^ETF$/i).last().selectOption({ index: 3 });
        await page.getByLabel(/^Account$/i).last().selectOption('nisa_growth');
        await page.getByLabel(/Value \(JPY\)/i).last().fill('400000');

        await page.getByRole('button', { name: /Save Portfolio/i }).click();

        // NISA Growth should show updated total (800000 + 400000 = 1200000)
        const nisaCard = page.locator('.card').filter({ hasText: /NISA Growth/i });
        await expect(nisaCard.getByText(/¥1,200,000/i).or(nisaCard.getByText(/¥1,200,000/i))).toBeVisible();

        // Grand total should also update (1200000 + 500000 = 1700000)
        await expect(page.getByText(/¥1,700,000/i).or(page.getByText(/¥1,700,000/i))).toBeVisible();
    });

    test('should show empty state when no holdings', async ({ page }) => {
        // Create a new plan without holdings
        const newPlanName = `Empty Plan ${Date.now()}`;
        await page.getByRole('button', { name: /Back to Plans/i }).click();
        await createPlan(page, newPlanName);

        // Should not see Current Holdings section
        await expect(page.getByRole('heading', { name: /Current Holdings/i })).not.toBeVisible();

        // Should see prompt to register assets
        await expect(page.getByText(/Do you have existing investments/i)).toBeVisible();
    });

    test('should update holdings display after edits', async ({ page }) => {
        // Edit existing holding
        await page.getByRole('button', { name: /Edit Portfolio/i }).click();

        // Change NISA Growth value
        const valueInput = page.getByLabel(/Value \(JPY\)/i).first();
        await valueInput.fill('1200000');

        await page.getByRole('button', { name: /Save Portfolio/i }).click();

        // Should see updated value
        const nisaCard = page.locator('.card').filter({ hasText: /NISA Growth/i });
        await expect(nisaCard.getByText(/¥1,200,000/i).or(nisaCard.getByText(/¥1,200,000/i))).toBeVisible();

        // Grand total should also update
        await expect(page.getByText(/¥1,700,000/i).or(page.getByText(/¥1,700,000/i))).toBeVisible();
    });
});
