import { test, expect } from '@playwright/test';
import { createPlan } from '../test-utils';

/**
 * PLAYGROUND FEATURE TESTS - PRESET HISTORICAL PERIODS
 * 
 * UI Labels:
 * - Selected preset buttons use btn-error class (not btn-primary)
 */

test.describe('Preset Historical Periods', () => {
    test.beforeEach(async ({ page }) => {
        // Create a unique plan for each test
        const planName = `Preset Periods Plan ${Date.now()}`;
        await createPlan(page, planName);

        // Navigate to Playground tab
        await page.getByRole('tab', { name: 'Playground' }).click();

        // Wait for page to stabilize
        await page.waitForTimeout(500);
    });

    test('should display preset period buttons', async ({ page }) => {
        // Should show all preset period buttons
        await expect(page.getByRole('button', { name: /Pre-COVID/i })).toBeVisible();
        await expect(page.getByRole('button', { name: /Pre-2008 Crisis/i })).toBeVisible();
        await expect(page.getByRole('button', { name: /Post-COVID Recovery/i })).toBeVisible();
        await expect(page.getByRole('button', { name: /5 Years Ago/i })).toBeVisible();
        await expect(page.getByRole('button', { name: /10 Years Ago/i })).toBeVisible();
    });

    test('should show icons on preset buttons', async ({ page }) => {
        // Buttons should have emoji icons (these appear as text in the button)
        const preCovidButton = page.getByRole('button', { name: /Pre-COVID/i });
        const buttonText = await preCovidButton.textContent();
        expect(buttonText).toMatch(/🦠/); // COVID icon
    });

    test('should populate date picker when clicking preset', async ({ page }) => {
        // Click Pre-COVID button
        await page.getByRole('button', { name: /Pre-COVID/i }).click();

        // Verify date input is populated with 2020-01-01
        const dateInput = page.locator('#start-date');
        await expect(dateInput).toHaveValue('2020-01-01');
    });

    test('should select 2008 crisis preset', async ({ page }) => {
        // Click Pre-2008 Crisis button
        await page.getByRole('button', { name: /Pre-2008 Crisis/i }).click();

        // Verify date input is populated with 2008-01-01
        const dateInput = page.locator('#start-date');
        await expect(dateInput).toHaveValue('2008-01-01');
    });

    test('should select "5 years ago" preset', async ({ page }) => {
        // Click 5 Years Ago button
        await page.getByRole('button', { name: /5 Years Ago/i }).click();

        // Verify date input is populated (approximately 5 years ago)
        const dateInput = page.locator('#start-date');
        const dateValue = await dateInput.inputValue();
        const selectedDate = new Date(dateValue);
        const now = new Date();
        const fiveYearsAgo = new Date(now.getFullYear() - 5, now.getMonth(), now.getDate());

        // Should be approximately 5 years ago (within a month)
        const diffInDays = Math.abs((selectedDate.getTime() - fiveYearsAgo.getTime()) / (1000 * 60 * 60 * 24));
        expect(diffInDays).toBeLessThan(31); // Within a month
    });

    test('should select "10 years ago" preset', async ({ page }) => {
        // Click 10 Years Ago button
        await page.getByRole('button', { name: /10 Years Ago/i }).click();

        // Verify date input is populated (approximately 10 years ago)
        const dateInput = page.locator('#start-date');
        const dateValue = await dateInput.inputValue();
        const selectedDate = new Date(dateValue);
        const now = new Date();
        const tenYearsAgo = new Date(now.getFullYear() - 10, now.getMonth(), now.getDate());

        // Should be approximately 10 years ago (within a month)
        const diffInDays = Math.abs((selectedDate.getTime() - tenYearsAgo.getTime()) / (1000 * 60 * 60 * 24));
        expect(diffInDays).toBeLessThan(31); // Within a month
    });

    test('should highlight selected preset', async ({ page }) => {
        // Click Pre-COVID
        await page.getByRole('button', { name: /Pre-COVID/i }).click();

        // Selected preset should have btn-error class
        const preCovidButton = page.getByRole('button', { name: /Pre-COVID/i });
        await expect(preCovidButton).toHaveClass(/btn-error/);

        // Click a different preset
        await page.getByRole('button', { name: /5 Years Ago/i }).click();

        // New preset should be highlighted
        const fiveYearsButton = page.getByRole('button', { name: /5 Years Ago/i });
        await expect(fiveYearsButton).toHaveClass(/btn-error/);

        // Previous preset should not be highlighted
        await expect(preCovidButton).not.toHaveClass(/btn-error/);
    });

    test('should allow changing preset selection', async ({ page }) => {
        // Click Pre-COVID
        await page.getByRole('button', { name: /Pre-COVID/i }).click();
        let dateInput = page.locator('#start-date');
        await expect(dateInput).toHaveValue('2020-01-01');

        // Change to 2008 Crisis
        await page.getByRole('button', { name: /Pre-2008 Crisis/i }).click();
        await expect(dateInput).toHaveValue('2008-01-01');

        // Change to 5 Years Ago
        await page.getByRole('button', { name: /5 Years Ago/i }).click();
        await expect(dateInput).not.toHaveValue('2008-01-01');
    });

    test('should show preset selection section header', async ({ page }) => {
        // Should show section label
        await expect(page.getByText(/Quick Select Historical Period/i)).toBeVisible();
    });

    test('should allow manual date override after selecting preset', async ({ page }) => {
        // Click a preset first
        await page.getByRole('button', { name: /Pre-COVID/i }).click();

        // Manually change the date
        const dateInput = page.locator('#start-date');
        await dateInput.fill('2019-07-15');

        // Verify the manual date override worked
        await expect(dateInput).toHaveValue('2019-07-15');
    });

    test('should show meaningful labels for each preset', async ({ page }) => {
        // Each button should have a descriptive label
        await expect(page.getByRole('button', { name: /Pre-COVID/i })).toBeVisible();
        await expect(page.getByRole('button', { name: /Pre-2008 Crisis/i })).toBeVisible();
        await expect(page.getByRole('button', { name: /Post-COVID Recovery/i })).toBeVisible();
    });

    test('should not allow future dates in presets', async ({ page }) => {
        // All presets should be in the past
        const dateInput = page.locator('#start-date');

        // Click each preset and verify date is in the past
        const presets = [/Pre-COVID/i, /Pre-2008 Crisis/i, /Post-COVID Recovery/i, /5 Years Ago/i, /10 Years Ago/i];

        for (const preset of presets) {
            await page.getByRole('button', { name: preset }).click();
            const dateValue = await dateInput.inputValue();
            const selectedDate = new Date(dateValue);
            const now = new Date();

            expect(selectedDate.getTime()).toBeLessThan(now.getTime());
        }
    });
});
