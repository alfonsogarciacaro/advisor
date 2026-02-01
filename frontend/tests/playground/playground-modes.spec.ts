import { test, expect } from '@playwright/test';
import { createPlan } from '../test-utils';

/**
 * PLAYGROUND FEATURE TESTS - PLAYGROUND MODES
 *
 * These tests verify the Playground & Historical Analysis feature.
 * 
 * UI Labels:
 * - Tab 1: "Historical Audit" (not "Historical Replay")
 * - Tab 2: "Scenario Lab" (not "Future Simulation")
 * - Button: "Run Fear Test" (not "Run Backtest")
 * - Selected items use btn-error class (not btn-primary)
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
        // Should show both tabs: Historical Audit and Scenario Lab
        const historicalTab = page.getByRole('tab', { name: /Historical Audit/i });
        await expect(historicalTab).toBeVisible();

        const scenarioTab = page.getByRole('tab', { name: /Scenario Lab/i });
        await expect(scenarioTab).toBeVisible();
    });

    test('should switch to Historical Audit mode', async ({ page }) => {
        // Historical Audit should be active by default
        const historicalTab = page.getByRole('tab', { name: /Historical Audit/i });
        await expect(historicalTab).toHaveClass(/tab-active/);

        // Should show historical audit content (use heading to distinguish from tab)
        await expect(page.getByRole('heading', { name: /Historical Audit/i })).toBeVisible();
    });

    test('should show Scenario Lab tab', async ({ page }) => {
        // Scenario Lab tab should be visible
        const scenarioTab = page.getByRole('tab', { name: /Scenario Lab/i });
        await expect(scenarioTab).toBeVisible();
    });

    test('should persist mode selection during session', async ({ page }) => {
        // Historical Audit should be active
        const historicalTab = page.getByRole('tab', { name: /Historical Audit/i });
        await expect(historicalTab).toHaveClass(/tab-active/);

        // Navigate away and back - mode should persist
        await page.getByRole('tab', { name: 'Overview' }).click();
        await page.waitForTimeout(300);
        await page.getByRole('tab', { name: 'Playground' }).click();

        // Historical Audit should still be active
        await expect(historicalTab).toHaveClass(/tab-active/);
    });

    test('should show appropriate action button for Historical Audit', async ({ page }) => {
        // Should show "Run Fear Test" button
        const runButton = page.getByRole('button', { name: /Run Fear Test/i });
        await expect(runButton).toBeVisible();
    });

    test('should show mode-specific help text', async ({ page }) => {
        // Historical Audit should have description about fear testing
        await expect(page.getByText(/Would you have sold/i)).toBeVisible();
    });

    test('should visually distinguish active mode', async ({ page }) => {
        const activeTab = page.getByRole('tab', { name: /Historical Audit/i });
        const scenarioTab = page.getByRole('tab', { name: /Scenario Lab/i });

        // Active tab should have different class
        await expect(activeTab).toHaveClass(/tab-active/);
        await expect(scenarioTab).not.toHaveClass(/tab-active/);
    });

    test('should show investment amount and date inputs in Historical Audit', async ({ page }) => {
        // Should have investment amount input
        await expect(page.locator('#investment-amount')).toBeVisible();

        // Should have start date input
        await expect(page.locator('#start-date')).toBeVisible();

        // Should have strategy selector heading
        await expect(page.getByText(/Strategy Template/i)).toBeVisible();
    });
});
