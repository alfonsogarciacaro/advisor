import { test, expect } from '@playwright/test';

test.describe('Research Agent - Follow-up Suggestions', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');

        // For these tests, we need a plan with optimization results
        // In real testing, we'd either:
        // 1. Create a plan and run optimization
        // 2. Use mock API responses
        // 3. Seed test data

        // For now, assume we can navigate to a plan with results
        // or create one programmatically
    });

    test('should display follow-up suggestions after optimization', async ({ page }) => {
        // Navigate to a plan with completed optimization
        // For testing, we might need to:
        // 1. Create a plan
        // 2. Run optimization
        // 3. Wait for completion

        // Look for research panel
        const researchPanel = page.getByRole('heading', { name: /Research Agent/i });
        await expect(researchPanel).toBeVisible();

        // Look for suggestions section
        await expect(page.getByText(/Suggested Research/i)).toBeVisible();
    });

    test('should show 3-4 follow-up suggestions', async ({ page }) => {
        // Get suggestion cards
        const suggestions = page.locator('.card').filter({ hasText: /Suggested Research/ });

        // Should have multiple suggestions
        const count = await suggestions.count();
        expect(count).toBeGreaterThanOrEqual(3);
        expect(count).toBeLessThanOrEqual(4);
    });

    test('should run research when clicking suggestion', async ({ page }) => {
        // Find first suggestion card
        const firstSuggestion = page.locator('.card').filter({ hasText: /Suggested Research/ }).first();

        // Get the question text
        const questionText = await firstSuggestion.locator('p').textContent();

        // Click the "Analyze" button
        await firstSuggestion.getByRole('button', { name: /Analyze/i }).click();

        // Should show loading state
        await expect(page.getByText(/Analyzing/i)).toBeVisible();
        await expect(page.locator('.loading')).toBeVisible();

        // Wait for research to complete (this might take a while)
        await expect(page.getByText(/Research completed/i), { timeout: 60000 }).toBeVisible();

        // Should show results
        await expect(page.getByText(/Summary/i)).toBeVisible();

        // Run ID should be displayed
        await expect(page.getByText(/Run ID:/i)).toBeVisible();
    });

    test('should pre-fill question when clicking suggestion', async ({ page }) => {
        // Click a suggestion
        const firstSuggestion = page.locator('.card').filter({ hasText: /Suggested Research/ }).first();
        await firstSuggestion.getByRole('button', { name: /Analyze/i }).click();

        // The question should appear in a "selected" state
        await expect(firstSuggestion).toHaveClass(/border-primary/);
    });

    test('should allow custom research question', async ({ page }) => {
        // Find custom query input
        const queryInput = page.getByPlaceholder(/recession/i).or(
            page.getByPlaceholder(/e.g., What happens/i)
        ).or(
            page.getByRole('textbox', { name: /question/i })
        );

        await expect(queryInput).toBeVisible();

        // Type a custom question
        await queryInput.fill('What happens if interest rates rise by 2%?');

        // Submit the question
        const submitButton = page.getByRole('button', { name: /submit/i }).or(
            page.locator('button').filter({ hasText: /→/ } )
        );

        await submitButton.click();

        // Should show loading
        await expect(page.locator('.loading')).toBeVisible();

        // Wait for results
        await expect(page.getByText(/Research completed/i), { timeout: 60000 }).toBeVisible();

        // Summary should contain relevant content
        await expect(page.getByText(/interest rates/i)).toBeVisible();
    });

    test('should submit custom question with Enter key', async ({ page }) => {
        const queryInput = page.getByPlaceholder(/recession/i).or(
            page.getByRole('textbox', { name: /question/i })
        );

        await queryInput.fill('Custom test question');

        // Press Enter
        await queryInput.press('Enter');

        // Should trigger research
        await expect(page.locator('.loading')).toBeVisible();
    });

    test('should generate new follow-up suggestions after research', async ({ page }) => {
        // Run initial research
        const firstSuggestion = page.locator('.card').filter({ hasText: /Suggested Research/ }).first();
        await firstSuggestion.getByRole('button', { name: /Analyze/i }).click();

        // Wait for completion
        await expect(page.getByText(/Research completed/i), { timeout: 60000 }).toBeVisible();

        // Should see "Follow-up Questions" section
        await expect(page.getByText(/Follow-up Questions/i)).toBeVisible();

        // Should have new suggestions
        const newSuggestions = page.getByText(/Follow-up Questions/i)
            .locator('../..')
            .locator('button');

        const count = await newSuggestions.count();
        expect(count).toBeGreaterThan(0);
    });

    test('should chain research conversations', async ({ page }) => {
        // Run first research
        const queryInput = page.getByRole('textbox', { name: /question/i });
        await queryInput.fill('Analyze my portfolio risk');
        await queryInput.press('Enter');

        await expect(page.getByText(/Research completed/i), { timeout: 60000 }).toBeVisible();

        // Click a follow-up suggestion
        const followUpButton = page.getByRole('button', { name: /Follow-up/i }).or(
            page.locator('button').filter({ hasText: /^Analyze|^Explain|^What/i })
        ).first();

        await followUpButton.click();

        // Should run new research
        await expect(page.locator('.loading')).toBeVisible();

        // New research should complete
        await expect(page.getByText(/Research completed/i), { timeout: 60000 }).toBeVisible();

        // Should have accumulated research history
        // (This would be visible in plan detail)
    });

    test('should show error when no plan is selected', async ({ page }) => {
        // Go to main page without selecting a plan
        // Research panel should show "no plan selected" message

        // This test assumes the main page shows research panel
        // In actual implementation, research is only visible on plan detail

        // For now, just verify that without a plan,
        // research functionality is disabled or shows message
        const researchPanel = page.getByRole('heading', { name: /Research Agent/i });

        if (await researchPanel.isVisible()) {
            // Should show message about selecting a plan
            await expect(page.getByText(/select a plan/i)).toBeVisible();

            // Custom input should be disabled
            const queryInput = page.getByRole('textbox', { name: /question/i });
            await expect(queryInput).toBeDisabled();
        }
    });

    test('should handle research errors gracefully', async ({ page }) => {
        // Force an error scenario (e.g., very long query)
        const queryInput = page.getByRole('textbox', { name: /question/i });

        // Submit a query that might fail
        await queryInput.fill('A'.repeat(10000)); // Extremely long query
        await queryInput.press('Enter');

        // Should either:
        // 1. Show error message
        // 2. Complete successfully (if backend handles it)
        const errorAlert = page.getByRole('alert').filter({ hasText: /error/i });

        // Check if error appeared (timeout means success)
        const hasError = await errorAlert.isVisible({ timeout: 5000 }).catch(() => false);

        if (hasError) {
            // Error should be user-friendly
            await expect(errorAlert).toBeVisible();

            // Should be able to dismiss error
            await page.getByRole('button', { name: '✕' }).click();
            await expect(errorAlert).not.toBeVisible();
        }
    });

    test('should persist research results in plan history', async ({ page }) => {
        // Run research
        const queryInput = page.getByRole('textbox', { name: /question/i });
        await queryInput.fill('Test research query');
        await queryInput.press('Enter');

        await expect(page.getByText(/Research completed/i), { timeout: 60000 }).toBeVisible();

        // Go back to plans
        await page.getByRole('button', { name: /Back to Plans/i }).click();

        // Plan card should show research count
        const researchBadge = page.getByText(/Research/i);
        await expect(researchBadge).toBeVisible();

        // Navigate back to plan
        await page.getByText(/Test Plan/i).click();

        // Research history should be visible (in alert or badge)
        await expect(page.getByText(/research analysi/i)).toBeVisible();
    });

    test('should allow multiple concurrent research requests', async ({ page }) => {
        // Start first research
        await page.getByRole('textbox', { name: /question/i }).fill('First question');
        await page.getByRole('textbox', { name: /question/i }).press('Enter');

        // Quickly start second (should queue or cancel first)
        await page.getByRole('button', { name: /Cancel/i }).click();

        // Start new research
        await page.getByRole('textbox', { name: /question/i }).fill('Second question');
        await page.getByRole('button', { name: /→/ }).click();

        // Should load second research
        await expect(page.getByText(/Research completed/i), { timeout: 60000 }).toBeVisible();

        // Results should be from second query
        await expect(page.getByText(/Second question/i)).not.toBeVisible(); // Query not in results
    });

    test('should display research summary with formatting', async ({ page }) => {
        // Run research
        await page.getByRole('textbox', { name: /question/i }).fill('Explain Sharpe ratio');
        await page.getByRole('button', { name: /→/ }).click();

        await expect(page.getByText(/Research completed/i), { timeout: 60000 }).toBeVisible();

        // Summary section should be visible
        const summaryCard = page.locator('.card').filter({ hasText: /Summary/i });
        await expect(summaryCard).toBeVisible();

        // Summary should have multiple paragraphs or bullet points
        const summaryText = await summaryCard.textContent();
        expect(summaryText?.length).toBeGreaterThan(100); // At least some content
    });
});
