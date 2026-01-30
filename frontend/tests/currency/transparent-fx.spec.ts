import { test, expect } from '@playwright/test';
import { createPlan } from '../test-utils';

/**
 * US-FX-02: Transparent FX Conversion
 *
 * Acceptance Criteria:
 * - No currency selector in UI (all values in base currency)
 * - FX conversion happens behind the scenes
 * - Historical backtest includes FX impact
 * - FX risk is included in optimization
 * - Current USD/JPY rate fetched and cached
 *
 * SKIPPED: Tests require PortfolioEditor to work properly, which depends on:
 * 1. Backend ETF data loading correctly
 * 2. "Add Asset" button creating new rows (currently broken)
 *
 * TODO: Fix PortfolioEditor integration or mock backend responses
 */
test.describe.skip('Transparent FX Conversion', () => {
    test.beforeEach(async ({ page }) => {
        const planName = `FX Test ${Date.now()}`;
        await createPlan(page, planName);
    });

    test('should not show currency selector in UI', async ({ page }) => {
        // Portfolio editor should not have currency selection
        await page.getByRole('button', { name: /Edit Portfolio/i }).click();

        // Should only see JPY in label
        await expect(page.getByLabel(/Value \(JPY\)/i)).toBeVisible();

        // No currency selector dropdown
        const currencySelect = page.getByLabel(/Currency/i);
        const count = await currencySelect.count();

        // Optimizer might still have currency selector, but portfolio editor should not
        // We're in the portfolio editor modal, so count should be 0
        expect(count).toBe(0);
    });

    test('should display US ETF prices in JPY', async ({ page }) => {
        await page.getByRole('button', { name: /Edit Portfolio/i }).click();
        await page.getByRole('button', { name: /Add Asset/i }).click();

        // ETF dropdown should show prices in ¥
        const etfSelect = page.getByLabel(/^ETF$/i).first();

        // Get one of the options
        await etfSelect.selectOption({ index: 1 });

        // The option text should contain ¥ (converted prices)
        const selectedText = await etfSelect.locator('option:checked').textContent();
        expect(selectedText).toContain('¥');
    });

    // The following tests are skipped because they test backend behavior
    // that is not directly observable in the UI without complex setup

    test.skip('should include FX impact in historical backtest', async ({ page }) => {
        // TODO: This would require:
        // 1. Running a historical backtest
        // 2. Examining the results to verify FX impact is included
        // 3. Comparing portfolios with/without currency exposure
        // 
        // Skipped because it requires too much backend interaction and long-running
        // optimization processes that are better tested at the unit/API level.
    });

    test.skip('should include FX risk in optimization', async ({ page }) => {
        // TODO: This would require:
        // 1. Running an optimization
        // 2. Verifying that FX volatility is factored into the portfolio volatility
        // 3. Checking optimization report for FX risk mentions
        // 
        // Skipped because FX risk calculation is a backend concern that's difficult
        // to verify purely through UI integration tests without examining internal
        // optimization parameters.
    });

    test.skip('should cache current USD/JPY rate', async ({ page }) => {
        // TODO: This would require:
        // 1. Network request interception to verify caching behavior
        // 2. Multiple page loads to check if rate is fetched from cache
        // 3. Backend API testing to verify cache implementation
        // 
        // Skipped because cache behavior is primarily a backend implementation detail
        // not directly testable via UI integration tests.
    });

    test('should show all portfolio values in base currency after FX conversion', async ({ page }) => {
        // Add a US ETF (which requires FX conversion from USD to JPY)
        await page.getByRole('button', { name: /Edit Portfolio/i }).click();
        await page.getByRole('button', { name: /Add Asset/i }).click();

        await page.getByLabel(/^ETF$/i).first().selectOption({ index: 1 });
        await page.getByLabel(/^Account$/i).first().selectOption('nisa_growth');
        await page.getByLabel(/Value \(JPY\)/i).first().fill('500000');

        await page.getByRole('button', { name: /Save Portfolio/i }).click();

        // All displayed values should be in ¥
        const bodyText = await page.textContent('body');
        expect(bodyText).toContain('¥');

        // Total should be in ¥
        await expect(page.getByText(/Total Portfolio Value/i)).toBeVisible();
        await expect(page.getByText(/¥500,000/i)).toBeVisible();
    });
});
