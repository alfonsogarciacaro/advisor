import { test, expect } from '@playwright/test';
import { createPlan } from '../test-utils';

/**
 * PLAYGROUND FEATURE TESTS - PLAYGROUND MODES
 *
 * These tests verify the Playground & Historical Analysis feature.
 */

test.describe('Playground Modes', () => {
    test.beforeEach(async ({ page }) => {
        // Create a unique plan for each test
        const planName = `Playground Modes Plan ${Date.now()}`;
        await createPlan(page, planName);

        // Navigate to Playground tab
        await page.getByRole('tab', { name: 'Playground' }).click();

        // Wait for page to stabilize
        await page.waitForTimeout(500);
    });

    test('should display mode switcher tabs', async ({ page }) => {
        // Should show both tabs: Historical Replay and Future Simulation (disabled)
        const historicalTab = page.getByRole('tab', { name: /Historical Replay/i });
        await expect(historicalTab).toBeVisible();

        const futureTab = page.getByRole('tab', { name: /Future Simulation/i });
        await expect(futureTab).toBeVisible();

        // Future Simulation should be disabled with "Coming Soon" badge
        await expect(futureTab).toHaveAttribute('disabled');
        await expect(page.getByText('Coming Soon')).toBeVisible();
    });

    test('should switch to Historical Replay mode', async ({ page }) => {
        // Historical Replay should be active by default
        const historicalTab = page.getByRole('tab', { name: /Historical Replay/i });
        await expect(historicalTab).toHaveClass(/tab-active/);

        // Should show historical replay content (use heading to distinguish from tab)
        await expect(page.getByRole('heading', { name: /Historical Replay/i })).toBeVisible();
        await expect(page.getByText(/how this strategy would have performed/i)).toBeVisible();
    });

    test('should show Future Simulation as disabled', async ({ page }) => {
        // Future Simulation tab should be disabled
        const futureTab = page.getByRole('tab', { name: /Future Simulation/i });
        await expect(futureTab).toHaveAttribute('disabled');

        // Should show "Coming Soon" badge
        await expect(page.getByText('Coming Soon')).toBeVisible();
    });

    test('should persist mode selection during session', async ({ page }) => {
        // Historical Replay should be active
        const historicalTab = page.getByRole('tab', { name: /Historical Replay/i });
        await expect(historicalTab).toHaveClass(/tab-active/);

        // Navigate away and back - mode should persist
        await page.getByRole('tab', { name: 'Overview' }).click();
        await page.waitForTimeout(300);
        await page.getByRole('tab', { name: 'Playground' }).click();

        // Historical Replay should still be active
        await expect(historicalTab).toHaveClass(/tab-active/);
    });

    test('should show appropriate action button for Historical Replay', async ({ page }) => {
        // Should show "Run Backtest" button
        const runButton = page.getByRole('button', { name: /Run Backtest/i });
        await expect(runButton).toBeVisible();
    });

    test('should show mode-specific help text', async ({ page }) => {
        // Historical Replay should have description
        await expect(page.getByText(/Test different investment strategies using historical data/i)).toBeVisible();
        await expect(page.getByText(/how they would have performed/i)).toBeVisible();
    });

    test('should visually distinguish active mode', async ({ page }) => {
        const activeTab = page.getByRole('tab', { name: /Historical Replay/i });
        const inactiveTab = page.getByRole('tab', { name: /Future Simulation/i });

        // Active tab should have different class
        await expect(activeTab).toHaveClass(/tab-active/);
        await expect(inactiveTab).not.toHaveClass(/tab-active/);
    });

    test('should show investment amount and date inputs in Historical Replay', async ({ page }) => {
        // Should have investment amount input
        const amountInput = page.getByLabel(/Investment Amount/i);
        await expect(amountInput).toBeVisible();

        // Should have start date input
        const dateInput = page.getByLabel(/Start Date/i);
        await expect(dateInput).toBeVisible();

        // Should have strategy selector
        await expect(page.getByText(/Strategy Template/i)).toBeVisible();
    });
});
