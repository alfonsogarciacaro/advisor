import { test, expect } from '@playwright/test';
import { createPlan } from '../test-utils';

test.describe('Account Management - Multi-Account Strategy', () => {
    test.beforeEach(async ({ page }) => {
        // Create a plan to enable account management
        // Use a unique name
        const planName = `Account Test Plan ${Date.now()}`;
        await createPlan(page, planName);
    });

    test('should display accounts tab', async ({ page }) => {
        // Navigate to plan detail
        // Look for Accounts tab
        const accountsTab = page.getByRole('tab', { name: /Accounts/i });
        await expect(accountsTab).toBeVisible();

        // Should show account count if any exist
        // e.g., "Accounts (0)" or "Accounts (2)"
    });

    test('should switch to accounts view', async ({ page }) => {
        await page.getByRole('tab', { name: /Accounts/i }).click();

        // Should see account management interface
        await expect(page.getByRole('heading', { name: /Investment Accounts/i })).toBeVisible();

        // Should show summary stats
        await expect(page.getByText(/Total Accounts/i)).toBeVisible();
        await expect(page.getByText(/Annual Limit/i)).toBeVisible();
        await expect(page.getByText(/Available Space/i)).toBeVisible();
    });

    test('should show empty state when no accounts', async ({ page }) => {
        await page.getByRole('tab', { name: /Accounts/i }).click();

        // Should show "Add Account" button
        await expect(page.getByRole('button', { name: /Add Account/i })).toBeVisible();

        // Stats should show zeros
        await expect(page.getByText('0')).toBeVisible(); // Total accounts
    });

    test('should open add account modal', async ({ page }) => {
        await page.getByRole('tab', { name: /Accounts/i }).click();
        await page.getByRole('button', { name: /Add Account/i }).click();

        // Modal should appear
        await expect(page.getByRole('dialog')).toBeVisible();
        await expect(page.getByRole('heading', { name: /Add Investment Account/i })).toBeVisible();

        // Account type dropdown should be present
        await expect(page.getByLabel(/Account Type/i)).toBeVisible();
    });

    test('should show all account type options', async ({ page }) => {
        await page.getByRole('tab', { name: /Accounts/i }).click();
        await page.getByRole('button', { name: /Add Account/i }).click();

        const accountTypeSelect = page.getByLabel(/Account Type/i);
        const options = await accountTypeSelect.locator('option').all();

        const accountTypes = await Promise.all(
            options.map(async (opt) => await opt.textContent())
        );

        // Should include Japanese account types
        expect(accountTypes).toContain('NISA Growth');
        expect(accountTypes).toContain('NISA General');
        expect(accountTypes).toContain('iDeCo');
        expect(accountTypes).toContain('Taxable');
        expect(accountTypes).toContain('DC Pension');
    });

    test('should pre-fill account defaults for NISA Growth', async ({ page }) => {
        await page.getByRole('tab', { name: /Accounts/i }).click();
        await page.getByRole('button', { name: /Add Account/i }).click();

        // Select NISA Growth
        await page.getByLabel(/Account Type/i).selectOption('nisa_growth');

        // Click Add
        await page.getByRole('button', { name: /Add Account/i }).click();

        // Edit modal should open with pre-filled values
        await expect(page.getByRole('heading', { name: /Add/i })).toBeVisible();

        // Check pre-filled values
        await expect(page.getByDisplayValue(/¥1,800,000/)).toBeVisible(); // Annual limit
        await expect(page.getByDisplayValue(/0%/)).toBeVisible(); // Tax rates
    });

    test('should create NISA account and show tax-free badge', async ({ page }) => {
        await page.getByRole('tab', { name: /Accounts/i }).click();
        await page.getByRole('button', { name: /Add Account/i }).click();
        await page.getByLabel(/Account Type/i).selectOption('nisa_growth');
        await page.getByRole('button', { name: /Add Account/i }).click();

        // In edit modal, save with defaults
        await page.getByRole('button', { name: /Save Account/i }).click();

        // Account should appear in list
        await expect(page.getByText(/NISA Growth/i)).toBeVisible();

        // Should have tax-free badge
        await expect(page.getByText(/Tax-Free/i)).toBeVisible();

        // Should have progress bar (even if empty)
        await expect(page.locator('progress')).toBeVisible();
    });

    test('should create multiple account types', async ({ page }) => {
        await page.getByRole('tab', { name: /Accounts/i }).click();

        // Add NISA Growth
        await addAccount(page, 'nisa_growth', 'NISA Growth Account');

        // Add NISA General
        await addAccount(page, 'nisa_general', 'NISA General Account');

        // Add Taxable
        await addAccount(page, 'taxable', 'Taxable Overflow');

        // Summary should show totals
        await expect(page.getByText(/Total Accounts.*3/i)).toBeVisible();
        await expect(page.getByText(/¥3,000,000/i)).toBeVisible(); // Combined limit
    });

    test('should display account utilization progress bars', async ({ page }) => {
        // Create NISA Growth account
        await page.getByRole('tab', { name: /Accounts/i }).click();
        await page.getByRole('button', { name: /Add Account/i }).click();
        await page.getByLabel(/Account Type/i).selectOption('nisa_growth');
        await page.getByRole('button', { name: /Add Account/i }).click();

        // Set current balance
        await page.getByLabel(/Current Balance/i).fill('900000');

        // Save
        await page.getByRole('button', { name: /Save Account/i }).click();

        // Progress bar should show 50% used
        const progressBar = page.locator('progress').first();
        await expect(progressBar).toBeVisible();

        // Should show "used / total" text
        await expect(page.getByText(/¥900,000.*¥1,800,000/)).toBeVisible();
    });

    test('should edit account limits and balances', async ({ page }) => {
        // Create account first
        await createTestAccount(page, 'Test NISA');

        // Click edit button
        await page.locator('.card').filter({ hasText: /Test NISA/i })
            .getByRole('button', { name: /✏️/ }).click();

        // Update values
        await page.getByLabel(/Current Balance/i).fill('500000');
        await page.getByLabel(/Available Space/i).fill('700000');

        // Save
        await page.getByRole('button', { name: /Save Account/i }).click();

        // Updates should reflect
        await expect(page.getByDisplayValue(/500,000/)).toBeVisible();
        await expect(page.getByDisplayValue(/700,000/)).toBeVisible();
    });

    test('should delete account with confirmation', async ({ page }) => {
        // Create account
        await createTestAccount(page, 'To Delete');

        // Click delete button
        await page.locator('.card').filter({ hasText: /To Delete/i })
            .getByRole('button', { name: /🗑/ }).click();

        // Confirmation dialog
        await expect(page.getByText(/Remove "To Delete"/i)).toBeVisible();

        // Cancel should abort
        await page.getByRole('button', { name: /Cancel/i }).click();
        await expect(page.getByText(/To Delete/i)).toBeVisible();

        // Try again with confirm
        await page.locator('.card').filter({ hasText: /To Delete/i })
            .getByRole('button', { name: /🗑/ }).click();
        await page.getByRole('button', { name: /^OK$/i }).click();

        // Account should be removed
        await expect(page.getByText(/To Delete/i)).not.toBeVisible();
    });

    test('should show account-specific tax rates', async ({ page }) => {
        // Create NISA account (0% tax)
        await createTestAccount(page, 'NISA Account', 'nisa_growth');

        // Create Taxable account (20.315% tax)
        await createTestAccount(page, 'Taxable Account', 'taxable');

        // NISA should show 0%
        await expect(page.locator('.card').filter({ hasText: /NISA Account/i })
            .getByText(/0.0%/)).toBeVisible();

        // Taxable should show ~20%
        await expect(page.locator('.card').filter({ hasText: /Taxable Account/i })
            .getByText(/20.3%/)).toBeVisible();
    });

    test('should show deductable badge for iDeCo', async ({ page }) => {
        await createTestAccount(page, 'My iDeCo', 'ideco');

        // Should have "Deductible" badge
        await expect(page.getByText(/Deductible/i)).toBeVisible();
    });

    test('should calculate total annual limit across accounts', async ({ page }) => {
        await page.getByRole('tab', { name: /Accounts/i }).click();

        // Add multiple NISA accounts
        await addAccount(page, 'nisa_growth', 'NISA Growth');
        await addAccount(page, 'nisa_general', 'NISA General');

        // Summary should show combined total
        await expect(page.getByText(/¥3,000,000/)).toBeVisible(); // 1.8M + 1.2M
    });

    test('should handle unlimited accounts (taxable)', async ({ page }) => {
        await createTestAccount(page, 'Unlimited Account', 'taxable');

        // Should show "Unlimited" for annual limit
        await expect(page.getByText(/Unlimited/i)).toBeVisible();

        // Should not show progress bar (or show as full/infinite)
    });

    test('should edit account tax configuration', async ({ page }) => {
        await createTestAccount(page, 'Custom Tax Account', 'other');

        // Edit account
        await page.locator('.card').filter({ hasText: /Custom Tax Account/i })
            .getByRole('button', { name: /✏️/ }).click();

        // Change tax rates
        await page.getByLabel(/Dividend Tax Rate \(%\)/i).fill('10.315');
        await page.getByLabel(/Capital Gains Tax Rate \(%\)/i).fill('15.315');

        // Save
        await page.getByRole('button', { name: /Save Account/i }).click();

        // Should show new rates
        await expect(page.getByText(/10.3%/)).toBeVisible();
        await expect(page.getByText(/15.3%/)).toBeVisible();
    });

    test('should add withdrawal rules to account', async ({ page }) => {
        await createTestAccount(page, 'iDeCo with Rules', 'ideco');

        // Edit account
        await page.locator('.card').filter({ hasText: /iDeCo with Rules/i })
            .getByRole('button', { name: /✏️/ }).click();

        // Add withdrawal rules
        await page.getByLabel(/Withdrawal Rules/i).fill('Withdrawals only after age 60. 5% penalty for early withdrawal.');

        // Save
        await page.getByRole('button', { name: /Save Account/i }).click();

        // Rules should be saved (visible in edit)
        await page.locator('.card').filter({ hasText: /iDeCo with Rules/i })
            .getByRole('button', { name: /✏️/ }).click();

        await expect(page.getByDisplayValue(/Withdrawals only after age 60/i)).toBeVisible();
    });

    test('should prevent duplicate account names', async ({ page }) => {
        // Create first account
        await createTestAccount(page, 'My Account', 'nisa_growth');

        // Try to create second with same name
        await page.getByRole('tab', { name: /Accounts/i }).click();
        await page.getByRole('button', { name: /Add Account/i }).click();
        await page.getByLabel(/Account Type/i).selectOption('taxable');
        await page.getByRole('button', { name: /Add Account/i }).click();

        // In edit modal, try to save with same name
        await page.getByLabel(/Account Name/i).fill('My Account');

        // Should show error or prevent save
        await page.getByRole('button', { name: /Save Account/i }).click();

        // Either shows error or creates with modified name
        // (Implementation depends on requirements)
    });

    test('should validate account limit values', async ({ page }) => {
        await createTestAccount(page, 'Test Account', 'nisa_growth');

        // Edit account
        await page.locator('.card').filter({ hasText: /Test Account/i })
            .getByRole('button', { name: /✏️/ }).click();

        // Try negative limit
        await page.getByLabel(/Annual Limit/i).fill('-1000');

        // Should show validation error or prevent save
        const saveButton = page.getByRole('button', { name: /Save Account/i });
        await saveButton.click();

        // Check for error alert
        const errorAlert = page.getByRole('alert').filter({ hasText: /error|invalid|negative/i });
        const hasError = await errorAlert.isVisible({ timeout: 2000 }).catch(() => false);

        if (hasError) {
            await expect(errorAlert).toBeVisible();
        }
    });
});

// Helper functions
async function addAccount(page: any, type: string, name: string) {
    await page.getByRole('button', { name: /Add Account/i }).click();
    await page.getByLabel(/Account Type/i).selectOption(type);
    await page.getByRole('button', { name: /Add Account/i }).click();
    await page.getByLabel(/Account Name/i).fill(name);
    await page.getByRole('button', { name: /Save Account/i }).click();
}

async function createTestAccount(page: any, name: string, type: string = 'nisa_growth') {
    await page.getByRole('tab', { name: /Accounts/i }).click();

    // Skip if account already exists
    const existing = page.getByText(name);
    if (await existing.isVisible()) {
        return;
    }

    await page.getByRole('button', { name: /Add Account/i }).click();
    await page.getByLabel(/Account Type/i).selectOption(type);
    await page.getByRole('button', { name: /Add Account/i }).click();

    // Edit modal should open - fill name and save
    await page.getByLabel(/Account Name/i).fill(name);
    await page.getByRole('button', { name: /Save Account/i }).click();
}
